# FastAPI Examples Guide

## Overview

This directory contains **10 comprehensive FastAPI examples** demonstrating TabernacleORM's capabilities in real-world scenarios.

## Examples List

### 1. E-commerce API (`fastapi_ecommerce.py`)
**Complexity**: ⭐⭐⭐⭐⭐

**Models**: Category, Product, User, Order, Review (5 models)

**Features**:
- Complex product filtering with multiple criteria
- Nested populate (products → category, orders → user)
- Order creation with automatic stock management
- Review system with rating aggregation
- Analytics endpoints (top products, category stats, user statistics)

**Key Endpoints**:
- `GET /products` - Advanced filtering, sorting, pagination
- `POST /orders` - Create order with stock validation
- `GET /analytics/top-products` - Top-rated products
- `GET /analytics/category-stats` - Product count and average price per category

**Run**: `uvicorn fastapi_ecommerce:app --port 8000`

---

### 2. Blog API (`fastapi_blog.py`)
**Complexity**: ⭐⭐⭐⭐⭐

**Models**: Author, Tag, Post, Comment, Follow (5 models)

**Features**:
- Nested comments (comments with replies)
- Follow system for authors
- Personalized feed based on followed authors
- Populate with field selection
- View counter and like system

**Key Endpoints**:
- `GET /posts/{slug}` - Get post with nested comments
- `GET /feed/{author_id}` - Personalized feed
- `POST /authors/{author_id}/follow` - Follow an author
- `GET /authors/{username}` - Author profile with recent posts

**Run**: `uvicorn fastapi_blog:app --port 8001`

---

### 3. Real Estate API (`fastapi_realestate.py`)
**Complexity**: ⭐⭐⭐⭐

**Models**: Property (1 model)

**Features**:
- **Geospatial queries** using Haversine formula
- Location-based search (find properties within radius)
- Distance calculation in kilometers
- Advanced filtering (price, bedrooms, amenities)

**Key Endpoints**:
- `GET /properties/nearby` - Find properties within radius
  - Parameters: `latitude`, `longitude`, `radius_km`, `min_price`, `max_price`
- `GET /properties/search` - Advanced search with multiple filters

**Run**: `uvicorn fastapi_realestate:app --port 8002`

---

### 4. Task Management API (`fastapi_tasks.py`)
**Complexity**: ⭐⭐⭐⭐

**Models**: Team, User, Project, Task (4 models)

**Features**:
- Task assignment system
- Project statistics (completion rate, status breakdown)
- Multi-level populate (task → user, task → project)
- Priority and status tracking

**Key Endpoints**:
- `GET /tasks` - List tasks with filters and populate
- `GET /projects/{project_id}/stats` - Project statistics

**Run**: `uvicorn fastapi_tasks:app --port 8003`

---

### 5. Social Media API (`fastapi_social.py`)
**Complexity**: ⭐⭐⭐

**Models**: User, Post (2 models)

**Features**:
- User feed with posts
- Like system
- Follower count tracking

**Key Endpoints**:
- `GET /feed/{user_id}` - Get user's feed

---

### 6. Analytics API (`fastapi_analytics.py`)
**Complexity**: ⭐⭐⭐

**Models**: Event (1 model)

**Features**:
- Event tracking with flexible metadata
- Event aggregation and summary
- Real-time analytics

**Key Endpoints**:
- `GET /analytics/summary` - Event summary by type

---

### 7. Multi-tenant SaaS API (`fastapi_saas.py`)
**Complexity**: ⭐⭐⭐⭐

**Models**: Tenant, Data (2 models)

**Features**:
- API key authentication
- Tenant isolation
- Per-tenant data management

**Key Endpoints**:
- `GET /data` - Get tenant data (requires API key header)

---

### 8. Messaging API (`fastapi_messaging.py`)
**Complexity**: ⭐⭐⭐⭐

**Models**: Conversation, Message (2 models)

**Features**:
- Conversation management
- Message history
- Participant tracking

**Key Endpoints**:
- `GET /conversations/{conv_id}/messages` - Get conversation messages

---

### 9. Inventory Management API (`fastapi_inventory.py`)
**Complexity**: ⭐⭐⭐

**Models**: Warehouse, Product (2 models)

**Features**:
- Multi-warehouse inventory
- Low stock alerts
- SKU management

**Key Endpoints**:
- `GET /inventory/low-stock` - Get low stock products

---

### 10. Booking System API (`fastapi_booking.py`)
**Complexity**: ⭐⭐⭐

**Models**: Resource, Booking (2 models)

**Features**:
- Resource booking
- Time slot management
- Booking status tracking

**Key Endpoints**:
- `GET /bookings/resource/{resource_id}` - Get resource bookings

---

## Common Patterns Demonstrated

### 1. Complex Queries
```python
# Multiple filters with chaining
products = await Product.find(query).where("price").gt(min_price).where("price").lt(max_price).sort("-rating").limit(20).exec()
```

### 2. Populate (Join)
```python
# Simple populate
posts = await Post.find().populate("author_id").exec()

# Populate with field selection
posts = await Post.find().populate("author_id", select=["username", "avatar"]).exec()

# Multiple populates
tasks = await Task.find().populate("assigned_to").populate("project_id").exec()
```

### 3. Aggregations
```python
# Count by category
events = await Event.findMany()
summary = {}
for event in events:
    summary[event.event_type] = summary.get(event.event_type, 0) + 1
```

### 4. Geospatial Queries
```python
# Calculate distance
distance = calculate_distance(lat1, lon1, lat2, lon2)

# Filter by distance
nearby = [p for p in properties if calculate_distance(...) <= radius_km]
```

### 5. Statistics
```python
# Calculate completion rate
done = len([t for t in tasks if t.status == "done"])
completion_rate = (done / len(tasks) * 100) if tasks else 0
```

## Running the Examples

### Prerequisites
```bash
pip install fastapi uvicorn tabernacleorm
```

### Run Individual Example
```bash
# E-commerce API
uvicorn fastapi_ecommerce:app --reload --port 8000

# Blog API
uvicorn fastapi_blog:app --reload --port 8001

# Real Estate API
uvicorn fastapi_realestate:app --reload --port 8002
```

### Access API Documentation
Each API has automatic Swagger documentation:
- E-commerce: http://localhost:8000/docs
- Blog: http://localhost:8001/docs
- Real Estate: http://localhost:8002/docs

## Testing the APIs

### Using curl
```bash
# Create a product
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Laptop","price":999.99,"category_id":"1","stock":10}'

# Search products
curl "http://localhost:8000/products?min_price=500&max_price=1500&sort_by=-price"

# Find nearby properties
curl "http://localhost:8002/properties/nearby?latitude=40.7128&longitude=-74.0060&radius_km=5"
```

### Using Python requests
```python
import requests

# Create a product
response = requests.post(
    "http://localhost:8000/products",
    json={
        "name": "Laptop",
        "price": 999.99,
        "category_id": "1",
        "stock": 10
    }
)
print(response.json())

# Search products
response = requests.get(
    "http://localhost:8000/products",
    params={"min_price": 500, "max_price": 1500}
)
print(response.json())
```

## Database Support

All examples work with any supported database. Just change the connection string:

```python
# SQLite (default)
db = connect("sqlite:///myapp.db")

# MongoDB
db = connect("mongodb://localhost:27017/myapp")

# PostgreSQL
db = connect("postgresql://user:pass@localhost/myapp")

# MySQL
db = connect("mysql://user:pass@localhost/myapp")
```

## Production Considerations

1. **Authentication**: Add JWT or OAuth2 authentication
2. **Validation**: Use Pydantic models for request validation
3. **Error Handling**: Implement proper error handlers
4. **Rate Limiting**: Add rate limiting middleware
5. **Caching**: Implement caching for frequently accessed data
6. **Logging**: Add comprehensive logging
7. **Testing**: Write unit and integration tests
8. **Documentation**: Expand API documentation

## Next Steps

- Explore `connection_examples.py` for database connection options
- Check `performance_benchmarks.py` for performance comparisons
- Review `database_mongodb.py` for MongoDB-specific features
- Read `FEATURES.md` for complete feature documentation
