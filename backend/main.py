from fastapi import FastAPI
from pydantic import BaseModel
from brain import run_ai_agent
from database import init_db, get_workspaces, add_workspace, delete_workspace

init_db()

app = FastAPI()

class UserQuery(BaseModel):
    text: str
    workspace: str = "General"

class WorkspaceRequest(BaseModel):
    name: str

@app.get("/")
def home():
    return {"status": "ClockAI Backend is Running", "message": "Your Agentic Schedule Negotiator is online."}

@app.get("/workspaces")
def get_all_workspaces():
    return get_workspaces()

@app.post("/workspaces")
def create_workspace(req: WorkspaceRequest):
    workspace_id = req.name.strip()
    add_workspace(workspace_id, req.name)
    return {"id": workspace_id, "name": req.name}

@app.delete("/workspaces/{workspace_id}")
def remove_workspace(workspace_id: str):
    delete_workspace(workspace_id)
    return {"status": "deleted", "workspace_id": workspace_id}

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
    uvicorn.run(app, host="192.168.85.22", port=8000)