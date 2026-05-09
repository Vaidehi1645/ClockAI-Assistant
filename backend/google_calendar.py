import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "google_token.json")

def get_access_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    
    with open(TOKEN_FILE, 'r') as f:
        tokens = json.load(f)
    
    if 'access_token' not in tokens:
        return None
    
    response = requests.post('https://oauth2.googleapis.com/token', data={
        'client_id': os.getenv("GOOGLE_CLIENT_ID"),
        'client_secret': os.getenv("GOOGLE_CLIENT_SECRET"),
        'refresh_token': tokens.get('refresh_token'),
        'grant_type': 'refresh_token'
    })
    
    if response.status_code == 200:
        new_tokens = response.json()
        new_tokens['refresh_token'] = tokens.get('refresh_token')
        with open(TOKEN_FILE, 'w') as f:
            json.dump(new_tokens, f)
        return new_tokens['access_token']
    
    return None

def create_calendar_event(title, date_str, time_str, duration_minutes=30, description=""):
    access_token = get_access_token()
    
    if not access_token:
        print("Google Calendar: Not authenticated. Run python google_auth.py first!")
        return None
    
    try:
        start_datetime = f"{date_str}T{time_str}:00"
        
        hour = int(time_str.split(':')[0])
        end_hour = (hour * 60 + duration_minutes) // 60
        end_minute = (hour * 60 + duration_minutes) % 60
        end_time = f"{date_str}T{end_hour:02d}:{end_minute:02d}:00"
        
        event = {
            "summary": title,
            "description": f"Created by ClockAI\n{description}",
            "start": {
                "dateTime": start_datetime,
                "timeZone": "Asia/Kolkata"
            },
            "end": {
                "dateTime": end_time,
                "timeZone": "Asia/Kolkata"
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 30},
                    {"method": "email", "minutes": 60}
                ]
            }
        }
        
        url = f"https://www.googleapis.com/calendar/v3/calendars/{CALENDAR_ID}/events"
        
        response = requests.post(url, json=event, headers={
            'Authorization': f'Bearer {access_token}'
        })
        
        if response.status_code == 200:
            print(f"Google Calendar: Event '{title}' created for {date_str} at {time_str}")
            return response.json()
        else:
            print(f"Google Calendar API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error creating calendar event: {e}")
        return None