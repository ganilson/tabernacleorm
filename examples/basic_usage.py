"""
Example usage of TabernacleORM.

Run this file to see TabernacleORM in action:
    python examples/basic_usage.py

This example demonstrates the basic usage of TabernacleORM.

"""

from tabernacleorm import (
    Database,
    Model,
    IntegerField,
    StringField,
    TextField,
    FloatField,
    BooleanField,
    DateTimeField,
    ForeignKey,
)


# ============================================
# 1. Initialize Database
# ============================================

print("=" * 50)
print("TabernacleORM - Basic Usage Example")
print("=" * 50)

# Create an in-memory SQLite database (or use a file path like "my_app.db")
db = Database(":memory:", echo=True)


# ============================================
# 2. Define Models
# ============================================

class Author(Model):
    """Author model for blog posts."""
    name = StringField(max_length=100, nullable=False)
    email = StringField(max_length=255, unique=True)
    bio = TextField(nullable=True)
    active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)


class Post(Model):
    """Blog post model."""
    title = StringField(max_length=200, nullable=False)
    content = TextField(nullable=False)
    author_id = ForeignKey(to="authors", on_delete="CASCADE")
    views = IntegerField(default=0)
    rating = FloatField(nullable=True)
    published = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)


# ============================================
# 3. Connect Models to Database
# ============================================

Author.set_database(db)
Post.set_database(db)

# Create tables
db.create_tables()


# ============================================
# 4. Create Records
# ============================================

print("\n" + "=" * 50)
print("Creating records...")
print("=" * 50)

# Create authors
author1 = Author.create(
    name="John Doe",
    email="john@example.com",
    bio="Python developer and writer"
)
print(f"Created: {author1}")

author2 = Author.create(
    name="Jane Smith",
    email="jane@example.com",
    bio="Data scientist and blogger"
)
print(f"Created: {author2}")

# Create posts
post1 = Post.create(
    title="Getting Started with Python",
    content="Python is a versatile programming language...",
    author_id=author1.id,
    published=True,
    rating=4.5
)
print(f"Created: {post1}")

post2 = Post.create(
    title="Advanced ORM Techniques",
    content="Learn how to use ORMs effectively...",
    author_id=author1.id,
    views=100,
    published=True
)

post3 = Post.create(
    title="Data Science Introduction",
    content="Data science combines statistics and programming...",
    author_id=author2.id,
    published=False
)


# ============================================
# 5. Query Records
# ============================================

print("\n" + "=" * 50)
print("Querying records...")
print("=" * 50)

# Get all authors
print("\nAll authors:")
for author in Author.all():
    print(f"  - {author.name} ({author.email})")

# Filter posts
print("\nPublished posts:")
published = Post.filter(published=True)
for post in published:
    print(f"  - {post.title} (views: {post.views})")

# Get single record
john = Author.get(name="John Doe")
print(f"\nFound author: {john.name}")

# Advanced filtering
print("\nPosts with views > 50:")
popular = Post.filter(views__gt=50)
for post in popular:
    print(f"  - {post.title}")

# Ordering
print("\nPosts ordered by title (descending):")
ordered = Post.all().order_by("-title")
for post in ordered:
    print(f"  - {post.title}")

# Count
total_posts = Post.all().count()
print(f"\nTotal posts: {total_posts}")


# ============================================
# 6. Update Records
# ============================================

print("\n" + "=" * 50)
print("Updating records...")
print("=" * 50)

# Update single record
post1.views += 50
post1.save()
print(f"Updated {post1.title} views to {post1.views}")

# Get and verify
updated_post = Post.get_by_id(post1.id)
print(f"Verified views: {updated_post.views}")


# ============================================
# 7. Delete Records
# ============================================

print("\n" + "=" * 50)
print("Deleting records...")
print("=" * 50)

# Delete unpublished posts
unpublished = Post.filter(published=False)
for post in unpublished:
    print(f"Deleting: {post.title}")
    post.delete()

# Verify
remaining = Post.all().count()
print(f"Remaining posts: {remaining}")


# ============================================
# 8. Chained Queries
# ============================================

print("\n" + "=" * 50)
print("Chained queries...")
print("=" * 50)

# Complex query
results = (
    Post.filter(published=True)
    .filter(views__gte=0)
    .order_by("-views")
    .limit(5)
)

print("Top published posts by views:")
for post in results:
    print(f"  - {post.title}: {post.views} views")


# ============================================
# 9. Cleanup
# ============================================

print("\n" + "=" * 50)
print("Cleanup...")
print("=" * 50)

db.disconnect()
print("Database connection closed.")

print("\n✅ Example completed successfully!")
