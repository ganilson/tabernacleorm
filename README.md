# TabernacleORM

TabernacleORM is a unified, asynchronous Object-Relational Mapper (ORM) for Python. It provides a single, consistent API to interact with MongoDB, PostgreSQL, MySQL, and SQLite.

Its design is heavily inspired by Mongoose (from the Node.js ecosystem), making it intuitive for developers familiar with JavaScript or those who prefer a fluent, document-oriented interface even when working with SQL databases.

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

## Mongoose-Like Experience

If you have used Mongoose in Node.js, TabernacleORM feels right at home.

| Mongoose (Node.js) | TabernacleORM (Python) |
|--------------------|------------------------|
| `const user = await User.create({ name: 'John' });` | `user = await User.create(name="John")` |
| `const user = await User.findOne({ email: '...' });` | `user = await User.findOne({"email": "..."})` |
| `const users = await User.find({ age: { $gt: 18 } });` | `users = await User.find({"age": {"$gt": 18}}).exec()` |
| `user.name = 'Jane'; await user.save();` | `user.name = "Jane"; await user.save()` |

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

### Connecting to read and write replicas

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

### 2. Desktop Applications (Tkinter)
You can use TabernacleORM in desktop apps to handle local data (SQLite) or cloud data (MongoDB/Postgres).
*Note: Since Tkinter is synchronous, run async ORM calls in a separate thread or use a loop integration library like `async_tkinter_loop`.*

### 3. AI and Data Scripts
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

## Future Roadmap

We are constantly working to make TabernacleORM more interesting and powerful:

-   **Auto-Migrations**: Dynamic schema diffing that automatically generates migration files (similar to Django/Alembic).
-   **GraphQL Integration**: Auto-generate GraphQL schemas from your Models.
-   **Rust Core**: Rewriting the serialization/deserialization layer in Rust for extreme performance.
-   **GUI Admin Panel**: A built-in admin interface to manage your data visually.

## Author & Sponsorship

**Author:** Ganilson Garcia
**Sponsored by:** Synctech

(Logos included in documentation package)