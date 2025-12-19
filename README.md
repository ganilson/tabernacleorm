# TabernacleORM

TabernacleORM is a unified, asynchronous Object-Relational Mapper (ORM) for Python. It provides a single, consistent API to interact with MongoDB, PostgreSQL, MySQL, and SQLite.

Its design is heavily inspired by Mongoose (from the Node.js ecosystem), making it intuitive for developers familiar with JavaScript or those who prefer a fluent, document-oriented interface even when working with SQL databases.

## ⭐ What's New in v2.1.0

TabernacleORM now includes **25+ new Mongoose-inspired features**:

- **Enhanced Populate**: Nested populations, field selection, match filters, and options
- **8 New Model Methods**: `findOneAndUpdate`, `findByIdAndUpdate`, `findOneAndDelete`, `findByIdAndDelete`, `exists`, `countDocuments`, `distinct`, `where`
- **15+ New QuerySet Methods**: `where`, `or_`, `and_`, `nor`, `gt`, `gte`, `lt`, `lte`, `in_`, `nin`, `regex`, `lean`, and more
- **MongoDB Replica Sets**: Full support with automatic failover and read distribution
- **7 Comprehensive Examples**: Complete test files demonstrating all features

👉 **[See FEATURES.md for complete documentation and examples](FEATURES.md)**

## Why TabernacleORM?

### The Problem
In the Python ecosystem, you typically choose an ORM based on your database:
- **SQLAlchemy/Tortoise ORM**: Great for SQL, but switching to NoSQL (MongoDB) involves rewriting everything using ODMantic or Motor.
- **MongoEngine/ODMantic**: Great for MongoDB, but no SQL support.
- **Django ORM**: Synchronous by default, deeply coupled to the framework.

### The Tabernacle Solution
TabernacleORM decouples your application logic from the underlying database engine. You write the same code whether you are storing data in PostgreSQL today or migrating to MongoDB tomorrow.

**Key Differentiators:**
1.  **Unified API**: Use `find()`, `create()`, `save()` regardless of the backend.
2.  **Async First**: Built on top of `asyncio` for high-performance, non-blocking applications.
3.  **Low Boilerplate**: Define models with simple Python classes. No complex session management or data mappers required for basic tasks.
4.  **Mongoose-Inspired**: Familiar API for JavaScript developers with powerful query building.

## Mongoose-Like Experience

If you have used Mongoose in Node.js, TabernacleORM feels right at home.

| Mongoose (Node.js) | TabernacleORM (Python) |
|--------------------|------------------------|
| `const user = await User.create({ name: 'John' });` | `user = await User.create(name="John")` |
| `const user = await User.findOne({ email: '...' });` | `user = await User.findOne({"email": "..."})` |
| `const users = await User.find({ age: { $gt: 18 } });` | `users = await User.find({"age": {"$gt": 18}}).exec()` |
| `user.name = 'Jane'; await user.save();` | `user.name = "Jane"; await user.save()` |
| `await User.findByIdAndUpdate(id, { $set: {...} });` | `await User.findByIdAndUpdate(id, {"$set": {...}})` |
| `const count = await User.countDocuments({ active: true });` | `count = await User.countDocuments({"active": True})` |
| `const categories = await Product.distinct('category');` | `categories = await Product.distinct("category")` |

## Database Connections

### Quick Start

```python
from tabernacleorm import connect

# SQLite (file or memory)
db = connect("sqlite:///myapp.db")
await db.connect()

# MongoDB
db = connect("mongodb://localhost:27017/myapp")
await db.connect()

# PostgreSQL
db = connect("postgresql://user:password@localhost:5432/myapp")
await db.connect()

# MySQL
db = connect("mysql://user:password@localhost:3306/myapp")
await db.connect()
```

👉 **[See connection_examples.py for detailed connection options](examples/connection_examples.py)**

## MongoDB Replica Sets

TabernacleORM provides **first-class support for MongoDB replica sets**, enabling high availability and read scalability:

### Benefits

✅ **Automatic Failover** - If primary fails, a secondary is automatically elected  
✅ **Read Scalability** - Distribute reads across multiple nodes (3x performance)  
✅ **Data Redundancy** - Multiple copies prevent data loss  
✅ **Zero Downtime** - Maintenance without stopping your application  

### Quick Start

```python
from tabernacleorm import connect

# Replica set connection (3 nodes)
db = connect(
    "mongodb://host1:27017,host2:27017,host3:27017/myapp?"
    "replicaSet=rs0&"
    "readPreference=secondaryPreferred&"
    "w=majority"
)
await db.connect()

# MongoDB Atlas (automatic replica set)
db = connect(
    "mongodb+srv://user:pass@cluster.mongodb.net/myapp?"
    "retryWrites=true&w=majority"
)
await db.connect()
```

### Read Preferences

- **`primary`** - All reads from primary (strongest consistency)
- **`secondary`** - All reads from secondaries (max scalability)
- **`secondaryPreferred`** - Prefer secondaries, fallback to primary (recommended)
- **`primaryPreferred`** - Prefer primary, fallback to secondaries
- **`nearest`** - Read from nearest node (lowest latency)

### Write Concerns

- **`w: 0`** - No acknowledgment (fastest, no guarantee)
- **`w: 1`** - Acknowledged by primary (default, good balance)
- **`w: majority`** - Acknowledged by majority (strongest durability)

### Performance Comparison

```
Single Instance:
- Read Throughput: 500 req/s
- Availability: 99.0%

3-Node Replica Set:
- Read Throughput: 1500 req/s (3x) ✅
- Availability: 99.99% ✅
- Automatic Failover: Yes ✅
```

👉 **[Complete MongoDB Replica Guide](MONGODB_REPLICAS.md)**

---

## 🎯 Read Replica Control (NEW)

Control **where reads are executed** at the endpoint level for optimal performance:

### Method 1: Decorators (Recommended)

```python
from fastapi import FastAPI
from tabernacleorm.decorators import read_from_primary, read_from_secondary

app = FastAPI()

# Critical data → PRIMARY
@app.get("/users/me")
@read_from_primary
async def get_current_user():
    user = await User.findById(user_id).exec()
    return user

# Searches → SECONDARY (3x performance)
@app.get("/products/search")
@read_from_secondary
async def search_products(query: str):
    products = await Product.find({"name": {"$regex": query}}).exec()
    return products

# Analytics → SECONDARY
@app.get("/stats/dashboard")
@read_from_secondary
async def get_dashboard():
    stats = await Order.aggregate([...])
    return stats
```

### Available Decorators

```python
from tabernacleorm.decorators import (
    read_from_primary,              # Force PRIMARY (critical data)
    read_from_secondary,            # Force SECONDARY (searches, analytics)
    read_from_secondary_preferred,  # Prefer SECONDARY (recommended default)
    read_from_nearest               # Nearest node (geo-distributed apps)
)
```

### When to Use

| Decorator | Use Case | Example |
|-----------|----------|---------|
| `@read_from_primary` | Critical data, just created | User account, orders |
| `@read_from_secondary` | Searches, analytics, reports | Product search, dashboard |
| `@read_from_secondary_preferred` | General reads (good default) | List products, books |
| `@read_from_nearest` | Global apps, lowest latency | CDN-like content |

### Performance Impact

```
Without replica control:
- PRIMARY: 1000 reads/s + 100 writes/s = OVERLOADED ❌

With replica control:
- PRIMARY: 100 critical reads/s + 100 writes/s ✅
- SECONDARY 1: 450 reads/s ✅
- SECONDARY 2: 450 reads/s ✅
Result: 3x read capacity, lower latency
```

👉 **[Complete Read Replica Guide](REPLICA_QUICKSTART.md)**

---

## Supported Engines

TabernacleORM supports the following engines through a plugin interface:

1.  **MongoDB** (via `motor`): Native JSON support, embedded documents, and replica sets.
2.  **PostgreSQL** (via `asyncpg`): High-performance SQL, robust transaction support.
3.  **MySQL** (via `aiomysql`): Standard MySQL support with connection pooling.
4.  **SQLite** (via `aiosqlite`): Zero-configuration file-based database for development and embedded apps.

Connection strings are auto-detected:
- `mongodb://localhost:27017/db`
- `postgresql://user:pass@localhost/db`
- `mysql://user:pass@localhost/db`
- `sqlite:///my_db.sqlite`

## Installation

```bash
pip install tabernacleorm

# Install with specific drivers
pip install tabernacleorm[mongodb]
pip install tabernacleorm[postgresql]
pip install tabernacleorm[mysql]
pip install tabernacleorm[all]
```

## Supported Python Versions

- Python 3.8
- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12+

## 🎯 Complete Example: Library Management System

We've created a **production-ready Library Management System** demonstrating all TabernacleORM features with FastAPI:

### Features
- ✅ **JWT Authentication** with role-based access (Admin, Librarian, Member)
- ✅ **6 Models** with relationships (User, Author, Category, Book, Loan, Reservation)
- ✅ **Clean Architecture** - Models, Services, Controllers separation
- ✅ **Advanced Queries** - Populate, GroupBy, Lookup demonstrations
- ✅ **20+ API Endpoints** with automatic Swagger documentation

### Quick Preview

```python
# Populate (Join) - Get books with author and category
books = await Book.find()\
    .populate("author_id")\
    .populate("category_id")\
    .exec()

# GroupBy - Statistics per category
stats = await BookService.get_category_statistics()

# Lookup - Most borrowed books
most_borrowed = await BookService.get_most_borrowed_books(10)
```

### Running the Example

```bash
cd examples/library_management
pip install -r requirements.txt
uvicorn app.main:app --reload
# Access: http://localhost:8000/docs
```

👉 **[Complete Library Management Guide](examples/library_management/README.md)**

---

## Usage Scenarios

### 1. High-Performance APIs (FastAPI)
TabernacleORM is ideal for FastAPI due to its async nature.

```python
from fastapi import FastAPI
from tabernacleorm import connect, disconnect
from my_app.models import User

app = FastAPI()

@app.on_event("startup")
async def startup():
    await connect("postgresql://user:pass@localhost/db").connect()

@app.on_event("shutdown")
async def shutdown():
    await disconnect()

@app.post("/users")
async def create_user(data: dict):
    user = await User.create(**data)
    return {"id": user.id}
```

### 2. Connecting to read and write replicas

```python
from fastapi import FastAPI
from tabernacleorm import connect

app = FastAPI()

@app.on_event("startup")
async def startup():
    db = connect(
        engine="postgresql",
        write={"url": "postgresql://master:5432/db"},
        read=[
            {"url": "postgresql://slave1:5432/db"},
            {"url": "postgresql://slave2:5432/db"}
        ]
    )
    await db.connect()
```

### 3. Desktop Applications (Tkinter)
You can use TabernacleORM in desktop apps to handle local data (SQLite) or cloud data (MongoDB/Postgres).
*Note: Since Tkinter is synchronous, run async ORM calls in a separate thread or use a loop integration library like `async_tkinter_loop`.*

### 4. AI and Data Scripts
For simple scripts, implementing an entire SQLAlchemy repository pattern is overkill. TabernacleORM allows quick data persistence.

```python
import asyncio
from tabernacleorm import connect
from models import TrainingLog

async def log_training_metrics(epoch, loss):
    db = connect("sqlite:///training.db")
    await db.connect()
    await TrainingLog.create(epoch=epoch, loss=loss)
    await db.disconnect()
```

---

## Production Deployment

### Environment Configuration

```python
import os
from tabernacleorm import connect

# Use environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
db = connect(DATABASE_URL)
await db.connect()
```

### MongoDB Atlas (Recommended)

```env
# .env file
DATABASE_URL=mongodb+srv://user:pass@cluster.mongodb.net/myapp?retryWrites=true&w=majority
```

### PostgreSQL with Connection Pool

```env
DATABASE_URL=postgresql://user:pass@prod-db:5432/myapp?min_size=10&max_size=20
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t myapp .
docker run -p 8000:8000 -e DATABASE_URL=mongodb://... myapp
```

### Best Practices

1. **Use Environment Variables** - Never hardcode credentials
2. **Connection Pooling** - Configure appropriate pool sizes
3. **Read Replicas** - Use `@read_from_secondary` for scalability
4. **Monitoring** - Track query performance and replica lag
5. **Backups** - Regular automated backups
6. **SSL/TLS** - Always use encrypted connections in production

---

## Future Roadmap

We are constantly working to make TabernacleORM more interesting and powerful:

-   **Auto-Migrations**: Dynamic schema diffing that automatically generates migration files (similar to Django/Alembic).
-   **GraphQL Integration**: Auto-generate GraphQL schemas from your Models.
-   **Rust Core**: Rewriting the serialization/deserialization layer in Rust for extreme performance.
-   **GUI Admin Panel**: A built-in admin interface to manage your data visually.

---

## 📖 Documentation & Resources

### Core Documentation
- **[FEATURES.md](FEATURES.md)** - Complete feature guide with 25+ Mongoose-inspired features
- **[MONGODB_REPLICAS.md](MONGODB_REPLICAS.md)** - MongoDB replica sets guide (high availability, read scalability)
- **[REPLICA_QUICKSTART.md](REPLICA_QUICKSTART.md)** - Quick start for read replica control
- **[READ_REPLICA_CONTROL.md](READ_REPLICA_CONTROL.md)** - Complete guide for controlling read replicas

### Examples
- **[Library Management System](examples/library_management/README.md)** - Production-ready FastAPI app with JWT, 6 models, MVC architecture
- **[FastAPI Examples](examples/FASTAPI_EXAMPLES.md)** - 10 complete APIs (e-commerce, blog, real estate, etc.)
- **[Connection Examples](examples/connection_examples.py)** - All database connection methods
- **[MongoDB Examples](examples/database_mongodb.py)** - MongoDB-specific features
- **[Performance Benchmarks](examples/performance_benchmarks.py)** - Performance comparisons

### Quick Links
- 🌟 [Library Management (Featured Example)](examples/library_management/README.md)
- 📚 [All Examples](examples/)
- 🔧 [PyPI Package](https://pypi.org/project/tabernacleorm/)
- 🐛 [GitHub Issues](https://github.com/ganilson/tabernacleorm/issues)

---

## Author & Sponsorship

**Author:** Ganilson Garcia
**Sponsored by:** Synctech

(Logos included in documentation package)