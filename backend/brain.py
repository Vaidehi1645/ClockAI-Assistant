import google.generativeai as genai
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from database import get_existing_schedules, add_schedule # Import our new helpers

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Mock existing data (Phase 1 local simulation)
EXISTING_SCHEDULE = [
    {"time": "10:00", "date": "2026-05-08", "title": "Existing Meeting"}
]

SYSTEM_INSTRUCTION = f"""
You are an Android Scheduling Agent. 
Current Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Today is: {datetime.now().strftime('%A')}

STRICT OUTPUT RULES:
1. Output ONLY a valid JSON ARRAY.
2. TIME: 24-hour format (HH:mm). 
3. DATE: YYYY-MM-DD.
4. DURATION: Always estimate duration in minutes.

SCHEMA:
[
  {{
    "workspaceId": "string",
    "action": "CREATE | DELETE | UPDATE",
    "data": {{
      "time": "HH:mm",
      "date": "YYYY-MM-DD",
      "duration_minutes": integer,
      "title": "string"
    }},
    "message": "Friendly confirmation message"
  }}
]
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

def supervisor_check(workspace, new_tasks):
    final_tasks = []
    conflicts = []
    
    for task in new_tasks:
        task_date = task['data'].get('date') or task['data'].get('day') or "today"
        db_schedules = get_existing_schedules(task_date, workspace)
        
        is_conflict = any(
            item['time'] == task['data']['time']
            for item in db_schedules
        )
        
        if is_conflict:
            conflicts.append(task)
        else:
            final_tasks.append(task)
            
    return final_tasks, conflicts

def run_ai_agent(workspace, user_input):
    # 1. AI Extraction
    response = model.generate_content(
        f"Workspace: {workspace}. {user_input}",
        generation_config={"response_mime_type": "application/json"}
    )
    
    # 2. Parse AI JSON
    extracted_tasks = json.loads(response.text)
    
    clean_tasks, messy_conflicts = supervisor_check(workspace, extracted_tasks)
    
    # 4. Final Output/Action
    print(f"--- PROCESSING: '{user_input}' ---")
    if messy_conflicts:
        for c in messy_conflicts:
            print(f"⚠️ CONFLICT: '{c['data']['title']}' at {c['data']['time']} is already taken!")
    
    if clean_tasks:
        for t in clean_tasks:
            success = add_schedule(
                workspace, 
                t['data']['title'], 
                t['data']['date'], 
                t['data']['time'], 
                t['data']['duration_minutes']
            )
            if success:
                print(f"✅ SAVED TO DB: {t['data']['title']} at {t['data']['time']}")

    return clean_tasks

if __name__ == "__main__":
    run_ai_agent("General", "Gym at 7am tomorrow, and an office meeting at 10am")