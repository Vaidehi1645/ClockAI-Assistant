import google.generativeai as genai
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_INSTRUCTION = f"""
You are an Android Scheduling Agent. 
Current Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Today is: {datetime.now().strftime('%A')}

STRICT OUTPUT RULES:
1. Output ONLY valid JSON.
2. TIME: Use 12-hour format (HH:mm). 
3. DATE: Use YYYY-MM-DD. If the user mentions "Tonight" and that time has already passed, set the date to tomorrow.
4. TITLE: Extract a concise title for the alarm.
5. WORKSPACE: If no workspace is provided, default to 'General'.

SCHEMA:
{{
  "workspaceId": "string",
  "action": "CREATE | DELETE | UPDATE",
  "data": {{
    "time": "HH:mm",
    "date": "YYYY-MM-DD",
    "title": "string",
    "duration_minutes": integer
  }},
  "message": "string"
}}
"""

# Create Gemini model
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

def test_brain(user_input):
    response = model.generate_content(
        user_input,
        generation_config={
            "response_mime_type": "application/json"
        }
    )

    print(response.text)

# Test prompt

if __name__ == "__main__":
    test_brain("Your Homework for Tonight (8:30 PM – 10:30 PM)")
