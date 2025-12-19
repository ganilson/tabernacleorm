
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from tabernacleorm import connect, Model, fields

# 1. Define Models

class Author(Model):
    name = fields.StringField(required=True)
    active = fields.BooleanField(default=True)
class Todo(Model):
    title = fields.StringField(required=True)
    completed = fields.BooleanField(default=False)
    author = fields.ForeignKey(Author, nullable=True)
    class Meta:
        collection = "todos"

# 2. Define Pydantic Schemas (for API validation)
class TodoCreate(BaseModel):
    title: str
    completed: bool = False
    AuthorId: Optional[str] = None

class TodoResponse(BaseModel):
    id: str
    title: str
    completed: bool
    AuthotId: Optional[str] = None
    
class AuthorResponse(BaseModel):
    id: str
    name: str
    active: bool


# 3. Create FastAPI App
app = FastAPI(title="TabernacleORM + FastAPI Demo")

# 4. Database Connection Events
@app.on_event("startup")
async def startup_db():
    # Connect to SQLite for this demo
    # For MongoDB: connect("mongodb://localhost:27017/todo_db")
    db = connect("mongodb://localhost:27017/tabernacle_example")
    await db.connect()
    


@app.on_event("shutdown")
async def shutdown_db():
    # Disconnect logic if needed
    pass

# 5. API Routes
@app.post("/authors", response_model=AuthorResponse)
async def create_author(name: str):
    new_author = await Author.create(name=name)
    return {
        "id": str(new_author.id),
        "name": new_author.name,
        "active": new_author.active
    }

@app.get("/authors", response_model=List[AuthorResponse])
async def list_authors():
    authors = await Author.findMany()
    return [
        {
            "id": str(a.id),
            "name": a.name,
            "active": a.active
        }
        for a in authors
    ]
    


    

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
    todos = await Todo.find()
    return [
        {
            "id": str(t.id),
            "title": t.title,
            "Author": t.author,
            "completed": t.completed
        }
        for t in todos
    ]

@app.get("/todos/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: str):
    todo = await Todo.findById(todo_id).populate("author")
    print(todo)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {
        "id": str(todo.id),
        "author": todo.author,
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
