"""
Example usage of TabernacleORM v2.0.

Run this file to see TabernacleORM in action:
    python examples/basic_usage.py
"""

import asyncio
from tabernacleorm import (
    connect, 
    disconnect,
    Model,
    fields
)

# 1. Define Models
class Author(Model):
    name = fields.StringField(required=True)
    email = fields.StringField(unique=True)
    bio = fields.TextField()

class Post(Model):
    title = fields.StringField(required=True)
    content = fields.TextField()
    author_id = fields.ForeignKey(Author)
    views = fields.IntegerField(default=0)
    published = fields.BooleanField(default=False)

async def main():
    print("=" * 50)
    print("TabernacleORM v2.0 - Basic Usage")
    print("=" * 50)

    # 2. Connect to Database (using SQLite in-memory for this example)
    print("\nConnecting to database...")
    db = connect("sqlite:///:memory:")
    await db.connect()
    
    # Create Tables (Manual creation for this simple script, usually handled by migrations)
    print("Creating tables...")
    await db.get_write_engine().executeRaw("""
        CREATE TABLE authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE,
            bio TEXT
        );
    """)
    await db.get_write_engine().executeRaw("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(255) NOT NULL,
            content TEXT,
            author_id INTEGER REFERENCES authors(id),
            views INTEGER DEFAULT 0,
            published BOOLEAN DEFAULT 0
        );
    """)
    
    # 3. Create Records
    print("\nCreating authors...")
    author1 = await Author.create(
        name="Ganilson Garcia",
        email="ganilson@example.com",
        bio="Creator of TabernacleORM"
    )
    print(f"Created: {author1.name} (ID: {author1.id})")

    author2 = await Author.create(
        name="Jane Doe",
        email="jane@example.com",
        bio="Tech Writer"
    )
    print(f"Created: {author2.name} (ID: {author2.id})")

    print("\nCreating posts...")
    post1 = await Post.create(
        title="Welcome to TabernacleORM",
        content="This is a unified async ORM.",
        author_id=author1.id,
        published=True,
        views=100
    )
    print(f"Created: {post1.title}")

    post2 = await Post.create(
        title="Async Python is Great",
        content="Non-blocking I/O rules!",
        author_id=author2.id,
        published=True,
        views=50
    )
    
    # 4. Query Records
    print("\nQuerying records...")
    
    # Find all published posts
    print("\nPublished Posts:")
    posts = await Post.find({"published": True}).exec()
    for p in posts:
        print(f"- {p.title} (Views: {p.views})")

    # Filter with operators (Mongoose style)
    print("\nPosts with > 60 views:")
    popular = await Post.find({"views": {"$gt": 60}}).exec()
    for p in popular:
        print(f"- {p.title}")

    # 5. Update Records
    print("\nUpdating record...")
    post1.views += 10
    await post1.save()
    print(f"Updated views for '{post1.title}': {post1.views}")

    # 6. Delete Records
    print("\nDeleting record...")
    await post2.delete()
    count = await Post.find().count()
    print(f"Remaining posts count: {count}")

    # Cleanup
    await disconnect()
    print("\n✅ Done!")

if __name__ == "__main__":
    asyncio.run(main())
