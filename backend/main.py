from fastapi import FastAPI
from pydantic import BaseModel
from brain import run_ai_agent

app = FastAPI()

class UserQuery(BaseModel):
    text: str
    workspace: str = "General"  # Default workspace

@app.get("/")
def home():
    return {"status": "ClockAI Backend is Running"}

@app.post("/process")
def process_text(query: UserQuery):
    result = run_ai_agent(query.workspace, query.text)
    return {"tasks": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.85.197", port=8000)