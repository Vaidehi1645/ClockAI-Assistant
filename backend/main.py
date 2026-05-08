from fastapi import FastAPI
from pydantic import BaseModel
from brain import run_ai_agent
from database import init_db

init_db()

app = FastAPI()

class UserQuery(BaseModel):
    text: str
    workspace: str = "General"

@app.get("/")
def home():
    return {"status": "ClockAI Backend is Running", "message": "Your Agentic Schedule Negotiator is online."}

@app.post("/process")
def process_text(query: UserQuery):
    try:
        result = run_ai_agent(query.workspace, query.text)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"type": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.236.46", port=8000)