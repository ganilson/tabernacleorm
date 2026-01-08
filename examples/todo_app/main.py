"""
FastAPI TODO Application
Demonstrates all TabernacleORM features:
- CRUD operations
- Complex queries with MongoDB-style operators
- Population (ForeignKey and OneToMany)
- Batch updates and deletions
- Aggregation

Switch database engines by changing config.DATABASE_URL
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from tabernacleorm import connect, get_connection
import config
from models import User, TodoList, TodoItem

# ==================== Pydantic Schemas ====================

class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int | str
    name: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TodoListCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    user_id: int | str

class TodoListResponse(BaseModel):
    id: int | str
    title: str
    description: str
    user_id: UserResponse | int | str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TodoItemCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    list_id: int | str
    priority: int = 0
    due_date: Optional[datetime] = None

class TodoItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[int] = None
    due_date: Optional[datetime] = None

class TodoItemResponse(BaseModel):
    id: int | str
    title: str
    description: str
    completed: bool
    priority: int
    list_id: TodoListResponse | int | str
    due_date: Optional[datetime]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# ==================== FastAPI App ====================

app = FastAPI(title="TODO App - TabernacleORM Demo")

@app.on_event("startup")
async def startup():
    """Initialize database connection"""
    print(f"Connecting to database: {config.DATABASE_URL}")
    connect(config.DATABASE_URL, auto_create=config.AUTO_CREATE_TABLES)
    await get_connection().connect()
    print("Database connected successfully!")

@app.on_event("shutdown")
async def shutdown():
    """Close database connection"""
    await get_connection().disconnect()

# ==================== User Endpoints ====================

@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    """Create a new user"""
    new_user = await User.create(name=user.name, email=user.email)
    return new_user.model_dump()

@app.get("/users", response_model=List[UserResponse])
async def list_users():
    """List all users"""
    users = await User.all().exec()
    return [u.model_dump() for u in users]

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int | str):
    """Get user by ID with populated todo lists"""
    user = await User.find({"id": user_id}).populate("todo_lists").first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.model_dump()

@app.delete("/users/{user_id}")
async def delete_user(user_id: int | str):
    """Delete user"""
    user = await User.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user.delete()
    return {"message": "User deleted successfully"}

# ==================== TodoList Endpoints ====================

@app.post("/lists", response_model=TodoListResponse)
async def create_list(todo_list: TodoListCreate):
    """Create a new todo list"""
    new_list = await TodoList.create(
        title=todo_list.title,
        description=todo_list.description,
        user_id=todo_list.user_id
    )
    return new_list.model_dump()

@app.get("/lists", response_model=List[TodoListResponse])
async def list_todo_lists(user_id: Optional[int | str] = None):
    """List all todo lists, optionally filtered by user"""
    if user_id:
        lists = await TodoList.find({"user_id": user_id}).populate("user_id").exec()
    else:
        lists = await TodoList.all().populate("user_id").exec()
    return [l.model_dump() for l in lists]

@app.get("/lists/{list_id}")
async def get_list(list_id: int | str, populate: bool = True):
    """Get todo list by ID, optionally with populated items"""
    query = TodoList.find({"id": list_id})
    if populate:
        query = query.populate("user_id")
    
    todo_list = await query.first()
    if not todo_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    result = todo_list.model_dump()
    # Convert items if populated
    if populate and hasattr(todo_list, 'items') and todo_list.items:
        result['items'] = [item.model_dump() if hasattr(item, 'model_dump') else item for item in todo_list.items]
    
    return result

@app.delete("/lists/{list_id}")
async def delete_list(list_id: int | str):
    """Delete todo list and all its items"""
    todo_list = await TodoList.get(id=list_id)
    if not todo_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    # Delete all items in this list
    await TodoItem.deleteMany({"list_id": list_id})
    await todo_list.delete()
    
    return {"message": "List and all items deleted successfully"}

# ==================== TodoItem Endpoints ====================

@app.post("/items", response_model=TodoItemResponse)
async def create_item(item: TodoItemCreate):
    """Create a new todo item"""
    new_item = await TodoItem.create(
        title=item.title,
        description=item.description,
        list_id=item.list_id,
        priority=item.priority,
        due_date=item.due_date
    )
    return new_item.model_dump()

@app.get("/items", response_model=List[TodoItemResponse])
async def list_items(
    list_id: Optional[int | str] = None,
    completed: Optional[bool] = None,
    priority_gte: Optional[int] = Query(None, description="Minimum priority (0=low, 1=medium, 2=high)")
):
    """
    List todo items with optional filters
    Demonstrates complex MongoDB-style queries that work on ALL engines
    """
    query_dict = {}
    
    if list_id is not None:
        query_dict["list_id"] = list_id
    
    if completed is not None:
        query_dict["completed"] = completed
    
    # Complex query using $gte operator (works on MongoDB, SQLite, PostgreSQL, MySQL!)
    if priority_gte is not None:
        query_dict["priority"] = {"$gte": priority_gte}
    
    items = await TodoItem.find(query_dict).sort("-priority", "created_at").exec()
    return [item.model_dump() for item in items]

@app.patch("/items/{item_id}", response_model=TodoItemResponse)
async def update_item(item_id: int | str, update: TodoItemUpdate):
    """Update a todo item"""
    item = await TodoItem.get(id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = update.model_dump(exclude_unset=True)
    
    # If marking as completed, set completed_at
    if update_data.get("completed") == True and not item.completed:
        update_data["completed_at"] = datetime.now()
    elif update_data.get("completed") == False:
        update_data["completed_at"] = None
    
    if update_data:
        await TodoItem.updateMany({"id": item_id}, {"$set": update_data})
        # Refetch to get updated data
        item = await TodoItem.get(id=item_id)
    
    return item.model_dump()

@app.delete("/items/{item_id}")
async def delete_item(item_id: int | str):
    """Delete a todo item"""
    item = await TodoItem.get(id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    await item.delete()
    return {"message": "Item deleted successfully"}

# ==================== Batch Operations ====================

@app.post("/lists/{list_id}/complete-all")
async def complete_all_items(list_id: int | str):
    """Batch update: mark all items in a list as completed"""
    count = await TodoItem.updateMany(
        {"list_id": list_id, "completed": False},
        {"$set": {"completed": True, "completed_at": datetime.now()}}
    )
    return {"message": f"Marked {count} items as completed"}

@app.delete("/lists/{list_id}/delete-completed")
async def delete_completed_items(list_id: int | str):
    """Batch delete: remove all completed items from a list"""
    count = await TodoItem.deleteMany({"list_id": list_id, "completed": True})
    return {"message": f"Deleted {count} completed items"}

# ==================== Aggregation & Stats ====================

@app.get("/lists/{list_id}/stats")
async def get_list_stats(list_id: int | str):
    """
    Get statistics about a todo list using aggregation
    Demonstrates Model.aggregate() working across all engines
    """
    # Count total items
    total = await TodoItem.find({"list_id": list_id}).count()
    
    # Count completed items
    completed = await TodoItem.find({"list_id": list_id, "completed": True}).count()
    
    # Get items by priority using complex queries
    high_priority = await TodoItem.find({
        "list_id": list_id,
        "priority": {"$gte": 2}
    }).count()
    
    # Get overdue items
    overdue = await TodoItem.find({
        "list_id": list_id,
        "completed": False,
        "due_date": {"$lt": datetime.now()}
    }).count()
    
    return {
        "total_items": total,
        "completed_items": completed,
        "pending_items": total - completed,
        "completion_rate": round((completed / total * 100) if total > 0 else 0, 1),
        "high_priority_items": high_priority,
        "overdue_items": overdue
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": config.DATABASE_URL.split("://")[0],
        "auto_create": config.AUTO_CREATE_TABLES
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
