"""
FastAPI Example 4: Task Management API
Demonstrates: assignments, status tracking, complex relationships
"""

from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI
from pydantic import BaseModel
from tabernacleorm import connect, Model, fields


class Team(Model):
    name = fields.StringField(required=True)
    description = fields.StringField()
    
    class Meta:
        collection = "teams"


class User(Model):
    username = fields.StringField(required=True, unique=True)
    email = fields.StringField(required=True)
    team_id = fields.ForeignKey(Team, nullable=True)
    
    class Meta:
        collection = "users"


class Project(Model):
    name = fields.StringField(required=True)
    description = fields.StringField()
    team_id = fields.ForeignKey(Team)
    status = fields.StringField(default="active")
    
    class Meta:
        collection = "projects"


class Task(Model):
    title = fields.StringField(required=True)
    description = fields.StringField()
    project_id = fields.ForeignKey(Project)
    assigned_to = fields.ForeignKey(User, nullable=True)
    status = fields.StringField(default="todo")  # todo, in_progress, done
    priority = fields.StringField(default="medium")  # low, medium, high
    due_date = fields.DateTimeField(nullable=True)
    created_at = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        collection = "tasks"


app = FastAPI(title="Task Management API")


@app.on_event("startup")
async def startup():
    db = connect("sqlite:///tasks.db")
    await db.connect()
    await Team.createTable()
    await User.createTable()
    await Project.createTable()
    await Task.createTable()


@app.get("/tasks")
async def list_tasks(
    project_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None
):
    """List tasks with filters and populate"""
    query = {}
    if project_id:
        query["project_id"] = project_id
    if assigned_to:
        query["assigned_to"] = assigned_to
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    
    tasks = await Task.find(query).populate("assigned_to").populate("project_id").exec()
    
    return [
        {
            "id": str(t.id),
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "assigned_to": t.assigned_to.username if hasattr(t.assigned_to, 'username') else None,
            "project": t.project_id.name if hasattr(t.project_id, 'name') else None
        }
        for t in tasks
    ]


@app.get("/projects/{project_id}/stats")
async def get_project_stats(project_id: str):
    """Get project statistics"""
    tasks = await Task.find({"project_id": project_id}).exec()
    
    stats = {
        "total": len(tasks),
        "by_status": {},
        "by_priority": {},
        "completion_rate": 0
    }
    
    for task in tasks:
        stats["by_status"][task.status] = stats["by_status"].get(task.status, 0) + 1
        stats["by_priority"][task.priority] = stats["by_priority"].get(task.priority, 0) + 1
    
    done = stats["by_status"].get("done", 0)
    stats["completion_rate"] = (done / len(tasks) * 100) if tasks else 0
    
    return stats


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
