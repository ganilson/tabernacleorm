# TODO App - TabernacleORM Example

A complete FastAPI TODO application demonstrating **all** TabernacleORM features:
- ✅ CRUD operations (Create, Read, Update, Delete)
- ✅ Complex MongoDB-style queries that work on **ALL** engines
- ✅ Population (ForeignKey & OneToMany relationships)
- ✅ Batch operations
- ✅ Aggregation & statistics
- ✅ **Engine-agnostic**: Switch databases by changing one line in config!

## Features Demonstrated

### 1. Multi-Engine Support
Works seamlessly with MongoDB, SQLite, PostgreSQL, and MySQL. **Just change the `DATABASE_URL` in config.py!**

### 2. Relationships
- `User` → `TodoList` (OneToMany)
- `TodoList` → `TodoItem` (OneToMany)
- ForeignKeys with `Union[int, str]` for cross-engine compatibility

### 3. Complex Queries
MongoDB-style operators work on ALL engines:
```python
# Get high-priority items (priority >= 2)
items = await TodoItem.find({"priority": {"$gte": 2}}).exec()

# Get overdue incomplete items
overdue = await TodoItem.find({
    "completed": False,
    "due_date": {"$lt": datetime.now()}
}).exec()
```

### 4. Population
Efficiently load related data:
```python
# Get user with all their todo lists
user = await User.find({"id": user_id}).populate("todo_lists").first()

# Get list with all its items
list = await TodoList.find({"id": list_id}).populate("items").first()
```

## Installation

### 1. Install Dependencies
```bash
cd examples/todo_app
pip install -r requirements.txt
```

### 2. Configure Database
Edit `config.py` and uncomment your preferred database:

```python
# MongoDB (default)
DATABASE_URL = "mongodb://localhost:27017/todo_app"

# OR SQLite
# DATABASE_URL = "sqlite:///todo_app.db"

# OR PostgreSQL
# DATABASE_URL = "postgresql://user:password@localhost/todo_app"

# OR MySQL
# DATABASE_URL = "mysql://user:password@localhost/todo_app"
```

**That's it!** The same code works on all engines.

### 3. Run the App
```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --reload
```

The API will be available at: http://localhost:8000

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Users
- `POST /users` - Create user
- `GET /users` - List all users
- `GET /users/{user_id}` - Get user with populated lists
- `DELETE /users/{user_id}` - Delete user

### Todo Lists
- `POST /lists` - Create todo list
- `GET /lists?user_id={id}` - List todo lists (optionally filtered by user)
- `GET /lists/{list_id}?populate=true` - Get list with populated items
- `DELETE /lists/{list_id}` - Delete list and all items

### Todo Items
- `POST /items` - Create todo item
- `GET /items?list_id={id}&completed={bool}&priority_gte={int}` - List items (with filters)
- `PATCH /items/{item_id}` - Update item
- `DELETE /items/{item_id}` - Delete item

### Batch Operations
- `POST /lists/{list_id}/complete-all` - Mark all items as completed
- `DELETE /lists/{list_id}/delete-completed` - Delete all completed items

### Statistics & Aggregation
- `GET /lists/{list_id}/stats` - Get list statistics (total, completed, overdue, etc.)

### Health
- `GET /health` - Health check & database info

## Example Usage

### 1. Create a User
```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

### 2. Create a Todo List
```bash
curl -X POST "http://localhost:8000/lists" \
  -H "Content-Type: application/json" \
  -d '{"title": "Shopping List", "description": "Groceries for the week", "user_id": 1}'
```

### 3. Add Todo Items
```bash
curl -X POST "http://localhost:8000/items" \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk", "list_id": 1, "priority": 2}'

curl -X POST "http://localhost:8000/items" \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy eggs", "list_id": 1, "priority": 1}'
```

### 4. Get High Priority Items
```bash
curl "http://localhost:8000/items?priority_gte=2"
```

### 5. Complete All Items in List
```bash
curl -X POST "http://localhost:8000/lists/1/complete-all"
```

### 6. Get List Statistics
```bash
curl "http://localhost:8000/lists/1/stats"
```

Response:
```json
{
  "total_items": 2,
  "completed_items": 2,
  "pending_items": 0,
  "completion_rate": 100.0,
  "high_priority_items": 1,
  "overdue_items": 0
}
```

## Switching Databases

### Testing with Different Engines

Want to verify it works on all engines? Just change `config.py`:

#### Test with SQLite
```python
# config.py
DATABASE_URL = "sqlite:///todo_app.db"
```
Restart the app - that's it!

#### Test with MongoDB
```python
# config.py
DATABASE_URL = "mongodb://localhost:27017/todo_app"
```
Restart the app - same code works!

#### Test with PostgreSQL
```python
# config.py
DATABASE_URL = "postgresql://user:password@localhost/todo_app"
```
```bash
pip install asyncpg
```
Restart - same code!

## Key Learning Points

### 1. Engine-Agnostic IDs
```python
# Works with both SQL (int) and NoSQL (str)
user_id: Optional[Union[int, str]] = ForeignKey("User")
```

### 2. MongoDB-Style Queries Everywhere
```python
# This query works on MongoDB, SQLite, PostgreSQL, AND MySQL!
items = await TodoItem.find({
    "priority": {"$gte": 2},
    "completed": False
}).exec()
```

### 3. Automatic Table Creation
```python
# config.py
AUTO_CREATE_TABLES = True

# Tables are created automatically on app startup!
```

### 4. Database Migrations (NEW in v2.1.5)
For production environments, you can manage your schema using the Tabernacle CLI:

```bash
# Register models and create migration
tabernacle makemigrations "initial"

# Apply to database
tabernacle migrate
```

### 4. Efficient Population
```python
# Load related data in ONE query (no N+1 problems)
list_with_items = await TodoList.find({"id": list_id}).populate("items").first()
```

### 5. Batch Operations
```python
# Update multiple records at once
await TodoItem.updateMany(
    {"list_id": list_id},
    {"$set": {"completed": True}}
)
```

## Project Structure
```
todo_app/
├── config.py       # Database configuration (CHANGE HERE to switch engines)
├── models.py       # User, TodoList, TodoItem models
├── main.py         # FastAPI application with all endpoints
├── requirements.txt
└── README.md
```

## Production Recommendations

1. **Environment Variables**: Move `DATABASE_URL` to environment variables
2. **Validation**: Add more comprehensive input validation
3. **Authentication**: Add JWT authentication for users
4. **Pagination**: Add pagination to list endpoints
5. **Error Handling**: Implement global error handlers
6. **Logging**: Add structured logging
7. **Testing**: Add pytest tests for all endpoints

## License

This example is part of TabernacleORM. See main repository for license.
