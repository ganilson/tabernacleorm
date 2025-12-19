# Read Replica Control - Complete Guide

## Overview

TabernacleORM provides **two methods** to control where reads are executed in a replica set:

1. **Query-level**: `.read_from()` method on queries
2. **Endpoint-level**: Decorators on FastAPI endpoints

## Method 1: Query-Level Control

### Usage

```python
from tabernacleorm import Model, fields

class Book(Model):
    title = fields.StringField()
    author = fields.StringField()
    
    class Meta:
        collection = "books"

# Force read from PRIMARY
book = await Book.findById(book_id).read_from("primary").exec()

# Force read from SECONDARY
books = await Book.find().read_from("secondary").exec()

# Prefer SECONDARY, fallback to PRIMARY
books = await Book.find().read_from("secondaryPreferred").exec()
```

### Read Preferences

| Preference | Description | Use Case |
|------------|-------------|----------|
| `primary` | Read from primary only | Critical data, just written |
| `secondary` | Read from secondary only | Analytics, searches |
| `secondaryPreferred` | Prefer secondary, fallback to primary | Most reads (recommended) |
| `primaryPreferred` | Prefer primary, fallback to secondary | High consistency needs |
| `nearest` | Read from nearest node | Geo-distributed apps |

### Example: FastAPI Endpoint

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/books/search")
async def search_books(query: str):
    # Search from SECONDARY (better performance)
    books = await Book.find(
        {"title": {"$regex": query}}
    ).read_from("secondary").exec()
    
    return books

@router.post("/orders")
async def create_order(order_data: dict):
    # Create order
    order = await Order.create(**order_data)
    
    # Read back from PRIMARY (ensure we see what we just created)
    created_order = await Order.findById(order.id).read_from("primary").exec()
    
    return created_order
```

### Advantages

✅ **Fine-grained control**: Different queries in same endpoint can use different preferences  
✅ **Explicit**: Clear which queries use which replicas  
✅ **Flexible**: Mix and match as needed  

### Disadvantages

❌ **Verbose**: Need to add `.read_from()` to every query  
❌ **Easy to forget**: Might miss some queries  

---

## Method 2: Endpoint-Level Decorators

### Usage

```python
from fastapi import APIRouter
from tabernacleorm.decorators import (
    read_from_primary,
    read_from_secondary,
    read_from_secondary_preferred
)

router = APIRouter()

@router.get("/books/search")
@read_from_secondary  # All queries in this endpoint use SECONDARY
async def search_books(query: str):
    # Automatically reads from SECONDARY
    books = await Book.find({"title": {"$regex": query}}).exec()
    return books

@router.get("/users/me")
@read_from_primary  # All queries in this endpoint use PRIMARY
async def get_current_user(user_id: str):
    # Automatically reads from PRIMARY
    user = await User.findById(user_id).exec()
    return user
```

### Available Decorators

```python
from tabernacleorm.decorators import (
    read_from_primary,           # Force PRIMARY
    read_from_secondary,         # Force SECONDARY
    read_from_secondary_preferred,  # Prefer SECONDARY
    read_from_nearest            # Nearest node
)

# Aliases (shorter)
from tabernacleorm.decorators import (
    read_primary,
    read_secondary,
    read_secondary_preferred,
    read_nearest
)
```

### Example: Complete API

```python
from fastapi import FastAPI, Depends
from tabernacleorm.decorators import (
    read_from_primary,
    read_from_secondary,
    read_from_secondary_preferred
)

app = FastAPI()

# ============================================
# CRITICAL DATA - PRIMARY
# ============================================

@app.get("/users/me")
@read_from_primary
async def get_current_user(current_user = Depends(get_current_user)):
    """User just logged in - must be up-to-date"""
    user = await User.findById(current_user.id).exec()
    return user

@app.post("/orders")
@read_from_primary
async def create_order(order_data: dict):
    """Just created - read from primary"""
    order = await Order.create(**order_data)
    return order

# ============================================
# SEARCHES - SECONDARY
# ============================================

@app.get("/products/search")
@read_from_secondary
async def search_products(query: str):
    """Search can use eventual consistency"""
    products = await Product.find({"name": {"$regex": query}}).exec()
    return products

@app.get("/books")
@read_from_secondary
async def list_books(category: str = None):
    """List operations - high volume"""
    query = {"category": category} if category else {}
    books = await Book.find(query).exec()
    return books

# ============================================
# ANALYTICS - SECONDARY
# ============================================

@app.get("/stats/dashboard")
@read_from_secondary
async def get_dashboard_stats():
    """Analytics don't need real-time data"""
    total_users = await User.count()
    total_orders = await Order.count()
    revenue = await Order.aggregate([...])
    
    return {
        "users": total_users,
        "orders": total_orders,
        "revenue": revenue
    }

# ============================================
# GENERAL READS - SECONDARY PREFERRED
# ============================================

@app.get("/products")
@read_from_secondary_preferred
async def list_products():
    """Good default - prefer secondary, fallback to primary"""
    products = await Product.find().exec()
    return products
```

### Advantages

✅ **Clean code**: Decorator at top, all queries inherit  
✅ **Declarative**: Clear intent of entire endpoint  
✅ **Less error-prone**: Can't forget individual queries  
✅ **Easy to change**: Change decorator, affects all queries  

### Disadvantages

❌ **Less flexible**: All queries in endpoint use same preference  
❌ **Can't mix**: If you need different preferences, use Method 1  

---

## Combining Both Methods

You can combine decorators with `.read_from()` for maximum flexibility:

```python
@app.get("/dashboard")
@read_from_secondary_preferred  # Default for endpoint
async def get_dashboard(user_id: str):
    # Critical user data - override to PRIMARY
    user = await User.findById(user_id).read_from("primary").exec()
    
    # Stats - use endpoint default (secondaryPreferred)
    stats = await Stats.find().exec()
    
    # Analytics - force SECONDARY
    reports = await Report.find().read_from("secondary").exec()
    
    return {
        "user": user,
        "stats": stats,
        "reports": reports
    }
```

---

## Decision Guide

### Use Query-Level (`.read_from()`) when:

- ✅ Different queries in same endpoint need different preferences
- ✅ Need fine-grained control
- ✅ Mixing critical and non-critical data

### Use Decorators when:

- ✅ All queries in endpoint have same requirements
- ✅ Want cleaner, more declarative code
- ✅ Endpoint purpose is clear (search, analytics, user data)

---

## Best Practices

### 1. User Account Data → PRIMARY

```python
@app.get("/users/me")
@read_from_primary
async def get_current_user():
    user = await User.findById(user_id).exec()
    return user
```

### 2. Just Created/Updated → PRIMARY

```python
@app.post("/books")
async def create_book(book_data: dict):
    book = await Book.create(**book_data)
    
    # Read back from primary
    created = await Book.findById(book.id).read_from("primary").exec()
    return created
```

### 3. Searches → SECONDARY

```python
@app.get("/search")
@read_from_secondary
async def search(query: str):
    results = await Product.find({"name": {"$regex": query}}).exec()
    return results
```

### 4. Analytics → SECONDARY

```python
@app.get("/analytics")
@read_from_secondary
async def get_analytics():
    stats = await Order.aggregate([...])
    return stats
```

### 5. General Reads → SECONDARY_PREFERRED

```python
@app.get("/products")
@read_from_secondary_preferred
async def list_products():
    products = await Product.find().exec()
    return products
```

---

## Performance Impact

### Without Read Replica Control

```
All reads from PRIMARY:
- Primary handles: 1000 reads/s + 100 writes/s
- Secondaries: Idle
- Latency: High (primary overloaded)
```

### With Read Replica Control

```
Reads distributed:
- Primary: 100 writes/s + 100 critical reads/s
- Secondary 1: 450 reads/s
- Secondary 2: 450 reads/s

Result:
- 3x read capacity
- Lower latency
- Primary focused on writes
```

---

## Configuration

### MongoDB Connection String

```env
# Replica set with read preference
DATABASE_URL=mongodb://host1:27017,host2:27017,host3:27017/db?replicaSet=rs0&readPreference=secondaryPreferred

# Override per query/endpoint
books = await Book.find().read_from("secondary").exec()
```

### PostgreSQL (Read Replicas)

```python
# Future support for PostgreSQL read replicas
db = connect(
    write="postgresql://primary:5432/db",
    read=["postgresql://replica1:5432/db", "postgresql://replica2:5432/db"]
)
```

---

## Summary

| Feature | Query-Level | Decorator |
|---------|-------------|-----------|
| Syntax | `.read_from("secondary")` | `@read_from_secondary` |
| Scope | Per query | Per endpoint |
| Flexibility | High | Medium |
| Code clarity | Medium | High |
| Error-prone | Medium | Low |
| Best for | Mixed requirements | Uniform requirements |

**Recommendation**: Use decorators for most endpoints, use `.read_from()` when you need to mix preferences within an endpoint.
