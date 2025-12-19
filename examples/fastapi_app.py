
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from tabernacleorm import connect, Model, fields

# 1. Define Models
class Todo(Model):
    title = fields.StringField(required=True)
    completed = fields.BooleanField(default=False)
    
    class Meta:
        collection = "todos"

# 2. Define Pydantic Schemas (for API validation)
class TodoCreate(BaseModel):
    title: str
    completed: bool = False

class TodoResponse(BaseModel):
    id: str
    title: str
    completed: bool

# 3. Create FastAPI App
app = FastAPI(title="TabernacleORM + FastAPI Demo")

# 4. Database Connection Events
@app.on_event("startup")
async def startup_db():
    # Connect to SQLite for this demo
    # For MongoDB: connect("mongodb://localhost:27017/todo_db")
    db = connect("mongodb://localhost:27017/tabernacle_example")
    await db.connect()
    
    # Ensure table exists (for SQL engines)
    await Todo.createTable()

@app.on_event("shutdown")
async def shutdown_db():
    # Disconnect logic if needed
    pass

# 5. API Routes
@app.post("/todos", response_model=TodoResponse)
async def create_todo(todo: TodoCreate):
    # Save to DB
    # Note: pydantic .dict() or .model_dump()
    data = todo.dict() if hasattr(todo, "dict") else todo.model_dump()
    new_todo = await Todo.create(**data)
    return {
        "id": str(new_todo.id),
        "title": new_todo.title,
        "completed": new_todo.completed
    }

@app.get("/todos", response_model=List[TodoResponse])
async def list_todos():
    # Query DB
    todos = await Todo.findMany()
    return [
        {
            "id": str(t.id),
            "title": t.title,
            "completed": t.completed
        }
        for t in todos
    ]

@app.get("/todos/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: str):
    todo = await Todo.findById(todo_id)
    print(todo)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {
        "id": str(todo.id),
        "title": todo.title,
        "completed": todo.completed
    }

@app.put("/todos/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: str, todo_update: TodoCreate):
    todo = await Todo.findById(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    todo.title = todo_update.title
    todo.completed = todo_update.completed
    await todo.save()
    
    return {
        "id": str(todo.id),
        "title": todo.title,
        "completed": todo.completed
    }

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: str):
    todo = await Todo.findById(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    await todo.delete()
    return {"message": "Deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
