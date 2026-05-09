import os
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "google_token.json")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/auth":
            self.send_response(302)
            auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={GOOGLE_CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=https://www.googleapis.com/auth/calendar&access_type=offline&prompt=consent"
            self.send_header('Location', auth_url)
            self.end_headers()
            
        elif parsed.path == "/auth/google/callback":
            code = parse_qs(parsed.query).get('code', [None])[0]
            if code:
                token_response = requests.post('https://oauth2.googleapis.com/token', data={
                    'code': code,
                    'client_id': GOOGLE_CLIENT_ID,
                    'client_secret': GOOGLE_CLIENT_SECRET,
                    'redirect_uri': REDIRECT_URI,
                    'grant_type': 'authorization_code'
                })
                if token_response.status_code == 200:
                    with open(TOKEN_FILE, 'w') as f:
                        json.dump(token_response.json(), f)
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"Success! Google Calendar connected. You can close this window.")
                else:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(f"Error: {token_response.text}".encode())
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"No code received")
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def start_auth_server():
    server = HTTPServer(('0.0.0.0', 3000), Handler)
    print("Google Auth Server running on http://localhost:3000/auth")
    print("Open this URL in browser to connect Google Calendar")
    server.serve_forever()

if __name__ == "__main__":
    start_auth_server()