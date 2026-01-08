# Quick Start: Read Replica Control

## Two Methods Available

### Method 1: Decorators (✅ Ready to use)

```python
from fastapi import FastAPI
from tabernacleorm.decorators import read_from_primary, read_from_secondary

app = FastAPI()

@app.get("/users/me")
@read_from_primary  # Critical data - read from PRIMARY
async def get_current_user():
    user = await User.findById(user_id).exec()
    return user

@app.get("/products/search")
@read_from_secondary  # Searches - read from SECONDARY
async def search_products(query: str):
    products = await Product.find({"name": {"$regex": query}}).exec()
    return products
```

### Method 2: Query-level (✅ Ready to use in v2.1.5)

```python
# Query-level control
books = await Book.find().read_from("secondary").exec()
user = await User.findById(id).read_from("primary").exec()
```

---

## Available Decorators

```python
from tabernacleorm.decorators import (
    read_from_primary,              # Force PRIMARY
    read_from_secondary,            # Force SECONDARY  
    read_from_secondary_preferred,  # Prefer SECONDARY, fallback PRIMARY
    read_from_nearest               # Nearest node (lowest latency)
)
```

---

## When to Use Each

### `@read_from_primary`
**Use for:**
- User account data
- Just created/updated records
- Critical consistency requirements

```python
@app.get("/users/me")
@read_from_primary
async def get_current_user():
    return await User.findById(user_id).exec()
```

### `@read_from_secondary`
**Use for:**
- Searches and listings
- Analytics and reports
- High-volume read endpoints

```python
@app.get("/products/search")
@read_from_secondary
async def search_products(query: str):
    return await Product.find({"name": {"$regex": query}}).exec()
```

### `@read_from_secondary_preferred` (Recommended default)
**Use for:**
- General read operations
- Good balance of performance and consistency

```python
@app.get("/books")
@read_from_secondary_preferred
async def list_books():
    return await Book.find().exec()
```

---

## Complete Example

```python
from fastapi import FastAPI, Depends
from tabernacleorm import connect
from tabernacleorm.decorators import (
    read_from_primary,
    read_from_secondary,
    read_from_secondary_preferred
)

app = FastAPI()

@app.on_event("startup")
async def startup():
    # Connect to MongoDB replica set
    db = connect(
        "mongodb://host1:27017,host2:27017,host3:27017/library?"
        "replicaSet=rs0&readPreference=secondaryPreferred"
    )
    await db.connect()

# CRITICAL DATA → PRIMARY
@app.get("/users/me")
@read_from_primary
async def get_current_user(current_user = Depends(get_current_user)):
    user = await User.findById(current_user.id).exec()
    return {"id": str(user.id), "username": user.username}

# SEARCHES → SECONDARY
@app.get("/books/search")
@read_from_secondary
async def search_books(query: str):
    books = await Book.find({"title": {"$regex": query}}).exec()
    return [{"id": str(b.id), "title": b.title} for b in books]

# ANALYTICS → SECONDARY
@app.get("/stats/dashboard")
@read_from_secondary
async def get_dashboard():
    total_books = await Book.count()
    total_users = await User.count()
    return {"books": total_books, "users": total_users}

# GENERAL READS → SECONDARY PREFERRED
@app.get("/books")
@read_from_secondary_preferred
async def list_books(skip: int = 0, limit: int = 20):
    books = await Book.find().skip(skip).limit(limit).exec()
    return books
```

---

## Configuration

### MongoDB Replica Set

```env
# .env file
DATABASE_URL=mongodb://host1:27017,host2:27017,host3:27017/library?replicaSet=rs0&readPreference=secondaryPreferred
```

### Connection String Options

```python
# Local replica set
mongodb://localhost:27017,localhost:27018,localhost:27019/db?replicaSet=rs0

# MongoDB Atlas
mongodb+srv://user:pass@cluster.mongodb.net/db?retryWrites=true&w=majority

# With read preference
mongodb://hosts/db?replicaSet=rs0&readPreference=secondaryPreferred&w=majority
```

---

## Performance Impact

### Before (all reads from PRIMARY)
```
PRIMARY: 1000 reads/s + 100 writes/s = OVERLOADED
SECONDARY 1: Idle
SECONDARY 2: Idle
```

### After (with decorators)
```
PRIMARY: 100 critical reads/s + 100 writes/s = HEALTHY
SECONDARY 1: 450 reads/s
SECONDARY 2: 450 reads/s

Result: 3x read capacity, lower latency
```

---

## See Also

- [Complete Guide](READ_REPLICA_CONTROL.md)
- [MongoDB Replicas Guide](MONGODB_REPLICAS.md)
- [Library Management Example](examples/library_management/app/controllers/replica_examples.py)
