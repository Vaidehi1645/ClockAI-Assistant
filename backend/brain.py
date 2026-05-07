import google.generativeai as genai
import os
import json
from datetime import datetime
from dotenv import load_dotenv

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

def supervisor_check(new_tasks):
    final_tasks = []
    conflicts = []
    
    for task in new_tasks:
        # Conflict check logic
        is_conflict = any(
            item['time'] == task['data']['time'] and 
            item['date'] == task['data']['date'] 
            for item in EXISTING_SCHEDULE
        )
        
        if is_conflict:
            conflicts.append(task)
        else:
            final_tasks.append(task)
            
    return final_tasks, conflicts

def run_ai_agent(user_input):
    # 1. AI Extraction
    response = model.generate_content(
        user_input,
        generation_config={"response_mime_type": "application/json"}
    )
    
    # 2. Parse AI JSON
    extracted_tasks = json.loads(response.text)
    
    # 3. Supervisor Validation
    clean_tasks, messy_conflicts = supervisor_check(extracted_tasks)
    
    # 4. Final Output/Action
    print(f"--- PROCESSING: '{user_input}' ---")
    if messy_conflicts:
        for c in messy_conflicts:
            print(f"⚠️ CONFLICT: '{c['data']['title']}' at {c['data']['time']} is already taken!")
            # Proactive Suggestion Logic could go here later
    
    if clean_tasks:
        for t in clean_tasks:
            print(f"✅ READY TO SYNC: {t['data']['title']} for {t['data']['date']} at {t['data']['time']}")
    
    return clean_tasks

if __name__ == "__main__":
    # Test a conflict scenario
    run_ai_agent("Gym at 7am tomorrow, and an office meeting at 10am")