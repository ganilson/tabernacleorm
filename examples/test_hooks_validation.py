"""
Test Hooks and Validation
Demonstrates pre/post hooks and custom validation
"""

import asyncio
from datetime import datetime
from tabernacleorm import connect, Model, fields


class BlogPost(Model):
    title = fields.StringField(required=True)
    content = fields.StringField(required=True)
    slug = fields.StringField(unique=True)
    view_count = fields.IntegerField(default=0)
    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(nullable=True)
    
    class Meta:
        collection = "blog_posts"
    
    # Pre-save hook: Auto-generate slug from title
    async def pre_save(self):
        """Generate slug before saving if not set."""
        if not self.slug:
            # Simple slug generation
            self.slug = self.title.lower().replace(" ", "-").replace("'", "")
            print(f"  🔧 Generated slug: {self.slug}")
        
        # Update timestamp
        if not self.is_new:
            self.updated_at = datetime.now()
            print(f"  🕒 Updated timestamp")
    
    # Post-save hook
    async def post_save(self):
        """Log after saving."""
        action = "created" if self.is_new else "updated"
        print(f"  ✅ Post {action}: {self.title}")
    
    # Pre-delete hook
    async def pre_delete(self):
        """Log before deleting."""
        print(f"  🗑️  Preparing to delete: {self.title}")
    
    # Post-delete hook
    async def post_delete(self):
        """Log after deleting."""
        print(f"  ✅ Deleted successfully")
    
    # Custom validation
    def validate(self):
        """Custom validation logic."""
        super().validate()  # Call parent validation first
        
        # Title must be at least 5 characters
        if len(self.title) < 5:
            raise ValueError("Title must be at least 5 characters long")
        
        # Content must be at least 20 characters
        if len(self.content) < 20:
            raise ValueError("Content must be at least 20 characters long")
        
        # Slug must not contain special characters (if set)
        if self.slug:
            allowed_chars = set("abcdefghijklmnopqrstuvwxyz0123456789-")
            if not all(c in allowed_chars for c in self.slug):
                raise ValueError("Slug can only contain lowercase letters, numbers, and hyphens")


class User(Model):
    username = fields.StringField(required=True, unique=True)
    email = fields.StringField(required=True, unique=True)
    password_hash = fields.StringField(required=True)
    login_count = fields.IntegerField(default=0)
    
    class Meta:
        collection = "users"
    
    # Pre-save hook: Hash password
    async def pre_save(self):
        """Simulate password hashing."""
        if self.is_new or self.is_modified("password_hash"):
            # In real app, use bcrypt or similar
            if not self.password_hash.startswith("hashed_"):
                self.password_hash = f"hashed_{self.password_hash}"
                print(f"  🔐 Password hashed for {self.username}")
    
    # Custom validation
    def validate(self):
        super().validate()
        
        # Username must be alphanumeric
        if not self.username.isalnum():
            raise ValueError("Username must be alphanumeric")
        
        # Email must contain @
        if "@" not in self.email:
            raise ValueError("Invalid email format")
        
        # Password must be at least 6 characters (before hashing)
        if not self.password_hash.startswith("hashed_") and len(self.password_hash) < 6:
            raise ValueError("Password must be at least 6 characters")


async def main():
    print("=" * 60)
    print("TabernacleORM - Hooks and Validation Test")
    print("=" * 60)
    
    # Connect
    db = connect("sqlite:///test_hooks.db")
    await db.connect()
    
    # Create tables
    print("\n📦 Creating tables...")
    await BlogPost.createTable()
    await User.createTable()
    
    # Test 1: Pre-save hook (slug generation)
    print("\n" + "=" * 60)
    print("Test 1: Pre-save Hook - Auto Slug Generation")
    print("=" * 60)
    print("Creating post without slug...")
    post1 = await BlogPost.create(
        title="My First Blog Post",
        content="This is the content of my first blog post. It's quite interesting!"
    )
    print(f"Result: slug = '{post1.slug}'")
    
    # Test 2: Pre-save hook (update timestamp)
    print("\n" + "=" * 60)
    print("Test 2: Pre-save Hook - Update Timestamp")
    print("=" * 60)
    print("Updating post...")
    post1.content = "Updated content with more information about the topic."
    await post1.save()
    print(f"Updated at: {post1.updated_at}")
    
    # Test 3: Post-save hook
    print("\n" + "=" * 60)
    print("Test 3: Post-save Hook - Logging")
    print("=" * 60)
    print("Creating another post...")
    post2 = await BlogPost.create(
        title="Second Post",
        content="This is my second blog post with different content."
    )
    
    # Test 4: Validation - Title too short
    print("\n" + "=" * 60)
    print("Test 4: Validation - Title Too Short")
    print("=" * 60)
    try:
        post3 = BlogPost(title="Hi", content="This content is long enough for validation.")
        post3.validate()
        print("❌ Validation should have failed!")
    except ValueError as e:
        print(f"✅ Validation failed as expected: {e}")
    
    # Test 5: Validation - Content too short
    print("\n" + "=" * 60)
    print("Test 5: Validation - Content Too Short")
    print("=" * 60)
    try:
        post4 = BlogPost(title="Valid Title", content="Short")
        post4.validate()
        print("❌ Validation should have failed!")
    except ValueError as e:
        print(f"✅ Validation failed as expected: {e}")
    
    # Test 6: Validation - Invalid slug
    print("\n" + "=" * 60)
    print("Test 6: Validation - Invalid Slug Characters")
    print("=" * 60)
    try:
        post5 = BlogPost(
            title="Valid Title Here",
            content="This is valid content that is long enough.",
            slug="invalid@slug!"
        )
        post5.validate()
        print("❌ Validation should have failed!")
    except ValueError as e:
        print(f"✅ Validation failed as expected: {e}")
    
    # Test 7: User pre-save hook (password hashing)
    print("\n" + "=" * 60)
    print("Test 7: Pre-save Hook - Password Hashing")
    print("=" * 60)
    print("Creating user with plain password...")
    user1 = await User.create(
        username="alice123",
        email="alice@example.com",
        password_hash="mypassword123"
    )
    print(f"Stored password: {user1.password_hash}")
    
    # Test 8: User validation - Invalid username
    print("\n" + "=" * 60)
    print("Test 8: Validation - Invalid Username")
    print("=" * 60)
    try:
        user2 = User(
            username="alice@123",
            email="alice2@example.com",
            password_hash="password"
        )
        user2.validate()
        print("❌ Validation should have failed!")
    except ValueError as e:
        print(f"✅ Validation failed as expected: {e}")
    
    # Test 9: User validation - Invalid email
    print("\n" + "=" * 60)
    print("Test 9: Validation - Invalid Email")
    print("=" * 60)
    try:
        user3 = User(
            username="bob123",
            email="invalidemail",
            password_hash="password"
        )
        user3.validate()
        print("❌ Validation should have failed!")
    except ValueError as e:
        print(f"✅ Validation failed as expected: {e}")
    
    # Test 10: Pre/Post delete hooks
    print("\n" + "=" * 60)
    print("Test 10: Pre/Post Delete Hooks")
    print("=" * 60)
    print("Deleting post...")
    await post2.delete()
    
    # Test 11: Multiple operations with hooks
    print("\n" + "=" * 60)
    print("Test 11: Multiple Operations")
    print("=" * 60)
    print("Creating, updating, and deleting...")
    temp_post = await BlogPost.create(
        title="Temporary Post",
        content="This post will be created, updated, and deleted."
    )
    temp_post.title = "Updated Temporary Post"
    await temp_post.save()
    await temp_post.delete()
    
    print("\n" + "=" * 60)
    print("✅ All hooks and validation tests completed!")
    print("=" * 60)
    
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
