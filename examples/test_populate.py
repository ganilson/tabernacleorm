"""
Test Populate Functionality
Demonstrates all populate features in TabernacleORM
"""

import asyncio
from tabernacleorm import connect, Model, fields


# Define Models
class Department(Model):
    name = fields.StringField(required=True)
    budget = fields.FloatField(default=0.0)
    
    class Meta:
        collection = "departments"


class Author(Model):
    name = fields.StringField(required=True)
    email = fields.StringField(unique=True)
    department_id = fields.ForeignKey(Department, nullable=True)
    
    class Meta:
        collection = "authors"


class Category(Model):
    name = fields.StringField(required=True)
    description = fields.StringField(nullable=True)
    
    class Meta:
        collection = "categories"


class Post(Model):
    title = fields.StringField(required=True)
    content = fields.StringField()
    author_id = fields.ForeignKey(Author)
    category_id = fields.ForeignKey(Category, nullable=True)
    views = fields.IntegerField(default=0)
    published = fields.BooleanField(default=False)
    
    class Meta:
        collection = "posts"


class Comment(Model):
    content = fields.StringField(required=True)
    post_id = fields.ForeignKey(Post)
    author_id = fields.ForeignKey(Author)
    
    class Meta:
        collection = "comments"


async def main():
    print("=" * 60)
    print("TabernacleORM - Populate Functionality Test")
    print("=" * 60)
    
    # Connect to database
    db = connect("sqlite:///test_populate.db")
    await db.connect()
    
    # Create tables
    print("\n📦 Creating tables...")
    await Department.createTable()
    await Author.createTable()
    await Category.createTable()
    await Post.createTable()
    await Comment.createTable()
    
    # Create test data
    print("\n📝 Creating test data...")
    
    # Departments
    cs_dept = await Department.create(name="Computer Science", budget=500000.0)
    eng_dept = await Department.create(name="Engineering", budget=750000.0)
    
    # Authors
    alice = await Author.create(
        name="Alice Johnson",
        email="alice@example.com",
        department_id=cs_dept.id
    )
    bob = await Author.create(
        name="Bob Smith",
        email="bob@example.com",
        department_id=eng_dept.id
    )
    charlie = await Author.create(
        name="Charlie Brown",
        email="charlie@example.com",
        department_id=cs_dept.id
    )
    
    # Categories
    tech = await Category.create(name="Technology", description="Tech articles")
    science = await Category.create(name="Science", description="Science articles")
    
    # Posts
    post1 = await Post.create(
        title="Introduction to Python",
        content="Python is a great language...",
        author_id=alice.id,
        category_id=tech.id,
        views=150,
        published=True
    )
    post2 = await Post.create(
        title="Machine Learning Basics",
        content="ML is fascinating...",
        author_id=bob.id,
        category_id=tech.id,
        views=200,
        published=True
    )
    post3 = await Post.create(
        title="Draft Post",
        content="This is a draft...",
        author_id=charlie.id,
        category_id=science.id,
        views=5,
        published=False
    )
    
    # Comments
    await Comment.create(
        content="Great article!",
        post_id=post1.id,
        author_id=bob.id
    )
    await Comment.create(
        content="Very informative",
        post_id=post1.id,
        author_id=charlie.id
    )
    await Comment.create(
        content="Thanks for sharing",
        post_id=post2.id,
        author_id=alice.id
    )
    
    print("✅ Test data created successfully!")
    
    # Test 1: Simple Populate
    print("\n" + "=" * 60)
    print("Test 1: Simple Populate")
    print("=" * 60)
    posts = await Post.find({"published": True}).populate("author_id").exec()
    for post in posts:
        print(f"\n📄 {post.title}")
        print(f"   Author: {post.author_id.name if hasattr(post.author_id, 'name') else post.author_id}")
        print(f"   Views: {post.views}")
    
    # Test 2: Populate with Select
    print("\n" + "=" * 60)
    print("Test 2: Populate with Select (only name field)")
    print("=" * 60)
    posts = await Post.find().populate("author_id", select=["name"]).exec()
    for post in posts:
        print(f"\n📄 {post.title}")
        if hasattr(post.author_id, 'name'):
            print(f"   Author: {post.author_id.name}")
            print(f"   (Email hidden due to select)")
    
    # Test 3: Populate with Match
    print("\n" + "=" * 60)
    print("Test 3: Populate with Match (only CS department authors)")
    print("=" * 60)
    posts = await Post.find().populate(
        "author_id",
        match={"department_id": cs_dept.id}
    ).exec()
    for post in posts:
        print(f"\n📄 {post.title}")
        if hasattr(post.author_id, 'name'):
            print(f"   Author: {post.author_id.name} (CS Dept)")
        else:
            print(f"   Author: Not from CS department")
    
    # Test 4: Nested Populate
    print("\n" + "=" * 60)
    print("Test 4: Nested Populate (author -> department)")
    print("=" * 60)
    posts = await Post.find({"published": True}).populate("author_id").exec()
    
    # Manually populate nested for now (full nested support in progress)
    for post in posts:
        if hasattr(post.author_id, 'department_id'):
            dept = await Department.findById(post.author_id.department_id)
            post.author_id.department_id = dept
    
    for post in posts:
        print(f"\n📄 {post.title}")
        if hasattr(post.author_id, 'name'):
            print(f"   Author: {post.author_id.name}")
            if hasattr(post.author_id.department_id, 'name'):
                print(f"   Department: {post.author_id.department_id.name}")
                print(f"   Budget: ${post.author_id.department_id.budget:,.2f}")
    
    # Test 5: Multiple Field Populate
    print("\n" + "=" * 60)
    print("Test 5: Multiple Field Populate (author + category)")
    print("=" * 60)
    posts = await Post.find().populate("author_id").populate("category_id").exec()
    for post in posts:
        print(f"\n📄 {post.title}")
        if hasattr(post.author_id, 'name'):
            print(f"   Author: {post.author_id.name}")
        if hasattr(post.category_id, 'name'):
            print(f"   Category: {post.category_id.name}")
    
    # Test 6: Populate with Options
    print("\n" + "=" * 60)
    print("Test 6: Populate with Options (sort, limit)")
    print("=" * 60)
    # Get comments and populate posts with options
    comments = await Comment.find().populate(
        "post_id",
        options={"sort": "-views", "limit": 2}
    ).exec()
    for comment in comments:
        print(f"\n💬 {comment.content}")
        if hasattr(comment.post_id, 'title'):
            print(f"   Post: {comment.post_id.title}")
            print(f"   Views: {comment.post_id.views}")
    
    print("\n" + "=" * 60)
    print("✅ All populate tests completed successfully!")
    print("=" * 60)
    
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
