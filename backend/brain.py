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

Today's date is {datetime.now().strftime('%Y-%m-%d')}.

Your task is to extract scheduling information from user input.

You MUST output ONLY valid JSON.

Detect one action:
- CREATE
- DELETE
- UPDATE
- QUERY

Rules:
- Convert relative dates like "tomorrow" into actual YYYY-MM-DD dates.
- Convert times into 12-hour HH:mm format.
- If no repeat is mentioned, return an empty array [].
- Repeat values can include:
  ["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]

Use this exact schema:

{{
  "action": "string",
  "date": "YYYY-MM-DD",
  "time": "HH:mm",
  "title": "string",
  "repeat": ["string"]
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