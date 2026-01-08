import asyncio
import sys
from typing import List, Optional, Union
from tabernacleorm import Model, connect
from tabernacleorm.fields import StringField, IntegerField, ForeignKey, OneToMany

# verify_sqlite.py: Same test but with SQLite to prove engine-agnostic design

async def verify_sqlite():
    print("--- Verifying TabernacleORM with SQLite ---")
    
    print("2. Defining Models...")
    try:
        class User(Model):
            name: str = StringField(max_length=50)
            age: int = IntegerField()
            posts: Optional[List["Post"]] = OneToMany("Post", back_populates="author_id")

        class Post(Model):
            title: str = StringField()
            rating: int = IntegerField(default=0)
            # SAME code works with SQLite!
            author_id: Optional[Union[int, str]] = ForeignKey("User")
            
        User.model_rebuild()
        print("   Models defined.")
    except Exception as e:
        print(f"[X] Model definition failed: {e}")
        return

    # 1. Connect - Just change URL to SQLite!
    print("1. DB Connection (SQLite)...")
    connect("sqlite:///:memory:", auto_create=True)
    from tabernacleorm import get_connection
    await get_connection().connect()

    # 3. Create Data
    print("3. Seeding Data...")
    try:
        alice = await User.create(name="Alice", age=30)
        bob = await User.create(name="Bob", age=25)
        
        await Post.create(title="Alice Post 1", rating=5, author_id=alice.id)
        await Post.create(title="Alice Post 2", rating=3, author_id=alice.id)
        await Post.create(title="Bob Post 1", rating=4, author_id=bob.id)
        
        print("   Data seeded.")
    except Exception as e:
        print(f"[X] Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # 4. Complex Queries - SAME syntax!
    print("4. Testing Complex Queries...")
    try:
        high_rated = await Post.find({"rating": {"$gt": 3}}).sort("-rating").exec()
        print(f"   High rated posts (>3): {[p.title for p in high_rated]}")
        
        assert len(high_rated) == 2
        print("   [OK] Operator Query ($gt) works on SQLite!")
        
        bob_posts = await Post.filter(author_id=bob.id).all()
        assert len(bob_posts) == 1
        print("   [OK] Simple Filter works on SQLite!")
        
    except Exception as e:
        print(f"[X] Complex Query failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n[SUCCESS] Same code works on both MongoDB and SQLite!")
    print("   Just change the connection URL to switch engines!")

if __name__ == "__main__":
    asyncio.run(verify_sqlite())
