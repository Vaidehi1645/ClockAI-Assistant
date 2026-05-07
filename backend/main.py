from fastapi import FastAPI
from pydantic import BaseModel
from brain import run_ai_agent

app = FastAPI()

class UserQuery(BaseModel):
    text: str

@app.get("/")
def home():
    return {"status": "ClockAI Backend is Running"}

@app.post("/process")
def process_text(query: UserQuery):
    # This calls your AI and Database logic
    result = run_ai_agent(query.text)
    return {"tasks": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.0.89", port=8000)