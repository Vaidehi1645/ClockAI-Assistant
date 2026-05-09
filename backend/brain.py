import google.generativeai as genai
import os
import json
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database import get_existing_schedules, get_all_schedules, add_schedule, init_db
from google_calendar import create_calendar_event

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

init_db()

GREETING_KEYWORDS = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'howdy', 'sup', "what's up"]

def is_greeting(text):
    cleaned = text.lower().strip().strip('?!.')
    return any(cleaned.startswith(kw) for kw in GREETING_KEYWORDS) and len(cleaned.split()) <= 3

SYSTEM_INSTRUCTION = """
You are a friendly Android Scheduling Agent. 
Today's date is: {today}

STRICT OUTPUT RULES:
1. Output ONLY a valid JSON ARRAY with tasks.
2. TIME: 24-hour format (HH:mm). 
3. DATE: Must be today ({today}) or a future date. NEVER use past dates.
4. DURATION: Always estimate duration in minutes (default 30).
5. PRIORITY: Use "high", "medium", or "low". Default to "medium".
6. If user mentions "override" or "overwrite" or "high priority", set priority to "high".

JSON SCHEMA:
[
  {{
    "workspaceId": "General",
    "action": "CREATE",
    "data": {{
      "time": "HH:mm",
      "date": "YYYY-MM-DD",
      "duration_minutes": 30,
      "title": "Task name",
      "priority": "high"
    }},
    "message": "Confirmation message"
  }}
]
""".format(today=datetime.now().strftime('%Y-%m-%d'))

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

def parse_date_safe(date_str):
    if not date_str:
        return datetime.now().strftime('%Y-%m-%d')
    try:
        parsed = datetime.strptime(str(date_str), '%Y-%m-%d')
        if parsed < datetime.now():
            return datetime.now().strftime('%Y-%m-%d')
        return parsed.strftime('%Y-%m-%d')
    except:
        return datetime.now().strftime('%Y-%m-%d')

def parse_time_safe(time_str):
    if not time_str:
        return None
    time_str = str(time_str).strip().lower()
    match = re.search(r'(\d{1,2})[:.](\d{2})\s*(am|pm)?', time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        period = match.group(3)
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"
    return None

def extract_json_from_response(text):
    text = text.strip()
    if text.startswith('['):
        try:
            return json.loads(text)
        except:
            pass
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    return None

def supervisor_check(workspace, new_tasks):
    final_tasks = []
    conflicts = []
    
    if not isinstance(new_tasks, list):
        new_tasks = [new_tasks]
    
    for task in new_tasks:
        if not isinstance(task, dict):
            continue
            
        task_data = task.get('data', {})
        task_time = parse_time_safe(task_data.get('time'))
        task_date = parse_date_safe(task_data.get('date'))
        
        if not task_time:
            conflicts.append({
                'task': task,
                'reason': 'No valid time specified'
            })
            continue
        
        all_schedules = get_all_schedules(task_date)
        
        conflicting_items = [
            item for item in all_schedules
            if item.get('time') == task_time
        ]
        
        task_priority = task_data.get('priority', 'medium')
        
        if conflicting_items:
            if task_priority == 'high':
                final_tasks.append(task)
                for conf in conflicting_items:
                    print(f"HIGH PRIORITY: Overwriting '{conf.get('title')}' at {task_time}")
            else:
                conflict_info = {
                    'task': task,
                    'conflicts': conflicting_items,
                    'message': f"I see a conflict with '{conflicting_items[0].get('title')}'. Should I overwrite it, schedule anyway, or set a priority?"
                }
                conflicts.append(conflict_info)
        else:
            final_tasks.append(task)
            
    return final_tasks, conflicts

def run_ai_agent(workspace, user_input):
    if not isinstance(user_input, str):
        return {'type': 'error', 'message': 'I can only process text. Please type your schedule request.'}
    
    if is_greeting(user_input):
        greetings = [
            "Hello! I'm ClockAI, your schedule assistant. Tell me what you'd like to plan today!",
            "Hi there! Ready to organize your day? What should I schedule?",
            "Hey! I'm here to help you manage your time. What needs to be done?"
        ]
        return {'type': 'greeting', 'message': greetings[datetime.now().second % len(greetings)]}
    
    try:
        response = model.generate_content(
            f"Workspace: {workspace}. {user_input}",
            generation_config={"response_mime_type": "application/json"}
        )
        
        print(f"AI Response: {response.text[:500]}")
        
        extracted_tasks = extract_json_from_response(response.text)
        
        if not extracted_tasks:
            return {'type': 'error', 'message': "I couldn't understand the schedule. Could you try one task at a time?"}
        
        if not isinstance(extracted_tasks, list):
            extracted_tasks = [extracted_tasks]
            
        clean_tasks, messy_conflicts = supervisor_check(workspace, extracted_tasks)
        
        print(f"--- PROCESSING: '{user_input}' ---")
        
        if messy_conflicts:
            conflict_response = []
            for c in messy_conflicts:
                task_title = c['task'].get('data', {}).get('title', 'Unknown') or c['task'].get('title', 'Unknown')
                conflict_titles = ', '.join([conf.get('title', 'Unknown') for conf in c.get('conflicts', [])])
                conflict_response.append({
                    'type': 'conflict',
                    'task': c['task'],
                    'message': f"I see a conflict with '{conflict_titles}'. Should I overwrite it, schedule anyway, or set a priority?"
                })
            return {'type': 'conflict', 'conflicts': conflict_response}
        
        saved_tasks = []
        if clean_tasks:
            for t in clean_tasks:
                task_data = t.get('data', t)
                title = task_data.get('title', 'Untitled')
                time_val = parse_time_safe(task_data.get('time'))
                date_val = parse_date_safe(task_data.get('date'))
                duration_val = task_data.get('duration_minutes', 30)
                
                if title and time_val:
                    is_high = task_data.get('priority', 'medium') == 'high'
                    success = add_schedule(
                        workspace, 
                        title, 
                        date_val, 
                        time_val, 
                        duration_val,
                        force=is_high
                    )
                    if success:
                        print(f"SAVED TO DB: {title} at {time_val}")
                        
                        calendar_result = create_calendar_event(
                            title, 
                            date_val, 
                            time_val, 
                            duration_val,
                            f"Workspace: {workspace}"
                        )
                        if calendar_result:
                            print(f"GCal: Event created - {calendar_result.get('htmlLink', '')}")
                        
                        saved_tasks.append(t)
        
        if saved_tasks:
            return {'type': 'success', 'tasks': saved_tasks}
        return {'type': 'no_tasks', 'message': 'No tasks were scheduled.'}
        
    except Exception as e:
        print(f"Error in run_ai_agent: {e}")
        import traceback
        traceback.print_exc()
        return {'type': 'error', 'message': 'Something went wrong. Please try again.'}

if __name__ == "__main__":
    result = run_ai_agent("General", "Gym at 7am tomorrow")
    print(result)