# TabernacleORM 2.1.4 🐍⚡

**The Async, Pydantic-powered ORM for Python.**

TabernacleORM is a modern, lightweight, and fully async Object-Relational Mapper (ORM) designed for **FastAPI** and modern Python applications. It supports **PostgreSQL**, **MySQL**, **SQLite**, and **MongoDB** with a unified, expressive API.

## Features

*   **Pydantic V2 Native**: Models are Pydantic models. Automatic validation, JSON serialization, and OpenAPI schema generation.
*   **Fully Async**: Built from the ground up for `asyncio`. No blocking IO.
*   **Unified API**: Switch between SQL and NoSQL databases without changing your business logic.
*   **Relationships**: `OneToMany`, `ManyToMany`, `ForeignKey` with lazy loading.
*   **Fluent Query Builder**: Write expressive queries like `User.filter(User.age > 18)`.
*   **Lifecycle Hooks**: `before_save`, `after_create`, etc., for powerful automation.
*   **Stateless Sessions**: Thread-safe and concurrency-safe session management.
*   **Read/Write Splitting**: Native support for replicas and high availability.

## Installation

```bash
pip install tabernacleorm
# For specific engines:
pip install tabernacleorm[postgresql]
pip install tabernacleorm[mysql]
pip install tabernacleorm[mongodb]
```

## Quickstart

### 1. Define your Models

Since Tabernacle models are Pydantic models, defining schemas is intuitive:

```python
from typing import Optional
from tabernacleorm import Model, connect
from tabernacleorm.fields import StringField, IntegerField, ForeignKey, OneToMany

# Connect to DB with auto table creation
connect("sqlite:///:memory:", auto_create=True)

class User(Model):
    name: str = StringField(max_length=50)
    age: int = IntegerField(default=18)
    
    # Relationships
    posts: list["Post"] = OneToMany("Post", back_populates="author_id")

    # Lifecycle Hooks
    async def before_save(self):
        self.name = self.name.capitalize()

class Post(Model):
    title: str = StringField()
    content: str = StringField()
    author_id: int = ForeignKey("User")
```

### 2. Create and Query

```python
import asyncio

async def main():
    # Create Tables (Handled by auto_create=True, or use migrations in prod)
    # await User.get_engine().executeRaw(User.get_create_table_sql())

    # Create Records
    user = await User.create(name="alice", age=30)
    await Post.create(title="Hello World", content="My first post", author_id=user.id)

    # Fluent Querying (Async)
    users = await User.filter(User.age > 20).all()
    
    # Eager Loading (New!)
    # Fetch users with their 'posts' in one go
    users_with_posts = await User.filter(User.age > 20).include("posts").all()

    # Lazy Loading (New!)
    my_posts = await user.fetch_related("posts")

    # Complex Filtering
    posts = await Post.filter(Post.title.startswith("Hello")).limit(5).all()

asyncio.run(main())
```

## Documentation

*   **[Feature Guide (FEATURES.md)](https://github.com/ganilson/tabernacleorm/blob/main/FEATURES.md)** - Detailed Mongoose-style features, advanced populate/include.
*   **[Read Replica Quickstart](https://github.com/ganilson/tabernacleorm/blob/main/REPLICA_QUICKSTART.md)** - Guide for using Read Replicas.
*   **[MongoDB Replicas](https://github.com/ganilson/tabernacleorm/blob/main/MONGODB_REPLICAS.md)** - High Availability guide.
*   **[Replica Control](https://github.com/ganilson/tabernacleorm/blob/main/READ_REPLICA_CONTROL.md)** - granular control over reads.

## New in 2.1.4: Weighted Load Balancing ⚖️

You can now assign weights to read replicas to distribute traffic according to server capacity.

```python
db = connect(
    engine="postgresql",
    write={"url": "postgresql://master:5432/db"},
    read=[
        # Heavy server gets 70% of traffic
        {"url": "postgresql://huge-replica:5432/db", "weight": 70},
        # Smaller server gets 30%
        {"url": "postgresql://small-replica:5432/db", "weight": 30}
    ]
)
```

## Advanced Features

### Transactions

Use the session context manager for safe transactions:

```python
engine = User.get_engine()
async with engine.transaction() as session:
    user = await User.create(name="Bob", age=25)
    # Pass session to save() to participate in transaction
    await Post.create(title="Intro", content="...", author_id=user.id, session=session)
```

### Hooks

Available hooks:
*   `before_save` / `after_save`
*   `before_create` / `after_create`
*   `before_delete` / `after_delete`

```python
class user(Model):
    password: str
    
    async def before_save(self):
        if not self.password.startswith("hash:"):
            self.password = f"hash:{self.password}"
```

### Relationships

Define relationships using `OneToMany`, `ManyToMany`, or standard `ForeignKey`.
Use `await instance.fetch_related("field_name")` to load them efficiently.

---
*Built with ❤️ by the Tabernacle Team.*