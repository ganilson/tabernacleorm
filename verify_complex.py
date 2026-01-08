import asyncio
import sys
from typing import List, Optional, Union
from tabernacleorm import Model, connect
from tabernacleorm.fields import StringField, IntegerField, ForeignKey, OneToMany

# verify_complex.py: Testing complex queries and population

async def verify_complex():
    print("1. DB Connection...")
    connect("sqlite:///:memory:", auto_create=True)

    # connect("mongodb://localhost:27017/complexy", auto_create=True)
    from tabernacleorm import get_connection
    await get_connection().connect()

    print("--- Verifying Complex Scenarios ---")
    
    print("2. Defining Models...")
    try:
        class User(Model):
            name: str = StringField(max_length=50)
            age: int = IntegerField()
            # One-to-Many: User has many Posts
            posts: Optional[List["Post"]] = OneToMany("Post", back_populates="author_id")

        class Post(Model):
            title: str = StringField()
            # ForeignKey now works with both SQL (int) and NoSQL (str) engines automatically
            rating: int = IntegerField(default=0)
            author_id: Optional[Union[int, str]] = ForeignKey("User")
            
        User.model_rebuild()
        # await User.create_table() # Handled by auto_create
        # await Post.create_table() # Handled by auto_create
        print("   Models defined.")
    except Exception as e:
        print(f"[X] Model definition failed: {e}")
        return

    # 1. Connect
    # Using sqlite memory for speed.
    # auto_create=True to ensure tables exist.
  
    # 3. Create Data
    print("3. Seeding Data...")
    try:
        # Clean existing data first
        await User.find().delete()
        await Post.find().delete()
        
        alice = await User.create(name="Alice", age=30)
        bob = await User.create(name="Bob", age=25)
        
        # Create posts for Alice
        await Post.create(title="Alice Post 1", rating=5, author_id=alice.id)
        await Post.create(title="Alice Post 2", rating=3, author_id=alice.id)
        
        # Create posts for Bob
        await Post.create(title="Bob Post 1", rating=4, author_id=bob.id)
        
        print("   Data seeded.")
    except Exception as e:
        print(f"[X] Seeding failed: {e}")
        return

    # 4. Complex Queries
    print("4. Testing Complex Queries...")
    try:
        # A. Filter with operators (Mongoose style)
        # Find posts with rating > 3
        high_rated = await Post.find({"rating": {"$gt": 3}}).sort("-rating").exec()
        print(f"   High rated posts (>3): {[p.title for p in high_rated]}")
        
        assert len(high_rated) == 2
        assert high_rated[0].title == "Alice Post 1" # Rating 5
        assert high_rated[1].title == "Bob Post 1"   # Rating 4
        print("   [OK] Operator Query ($gt)")

        # B. Filter with simple kwargs
        bob_posts = await Post.filter(author_id=bob.id).all()
        assert len(bob_posts) == 1
        print("   [OK] Simple Filter")
        
    except Exception as e:
        print(f"[X] Complex Query failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # 5. Complex Population
    print("5. Testing Complex Population...")
    try:
        # A. Populate ForeignKey (BelongsTo)
        # Fetch post and populate author
        post = await Post.find({"title": "Alice Post 1"}).populate("author_id").first()
        # Expect author_id to be replaced by User object, OR placed in a virtual field?
        # Current implementation replaces the field value if names match.
        # "author_id" field is int. Using populate("author_id") swaps it for User obj.
        if isinstance(post.author_id, User):
            print(f"   [OK] FK Population: Post by {post.author_id.name}")
        else:
            print(f"   [FAIL] FK Population: author_id is {type(post.author_id)}")

        # B. Populate OneToMany (Reverse)
        # Fetch User and populate posts
        # This requires .populate("posts")
        # "posts" is the OneToMany field name.
        print("   Testing Reverse Population (User.posts)...")
        alice_loaded = await User.find({"name": "Alice"}).populate("posts").first()
        
        if hasattr(alice_loaded, "posts") and alice_loaded.posts:
            print(f"   Alice's posts: {len(alice_loaded.posts)}")
            assert len(alice_loaded.posts) == 2
            print("   [OK] Reverse Population")
        else:
            print(f"   [FAIL] Reverse Population: posts attribute is {getattr(alice_loaded, 'posts', 'MISSING')}")

    except Exception as e:
        print(f"[X] Population failed: {e}")
        import traceback
        traceback.print_exc()

    # 6. Update
    print("6. Testing Update...")
    try:
        # Update Alice's age
        # findOneAndUpdate style or filter().update()
        # QuerySet.update() is batch update.
        affected = await User.filter(name="Alice").update({"age": 31})
        print(f"   Updated {affected} records.")
        assert affected >= 1
        
        alice_new = await User.find({"name": "Alice"}).first()
        assert alice_new.age == 31
        print("   [OK] Update Successful")
        
    except Exception as e:
         print(f"[X] Update failed: {e}")

    # 7. Pagination
    print("7. Testing Pagination...")
    try:
        # Create dummy data
        print("   Creating 50 dummy posts...")
        posts_data = [{"title": f"Post {i}", "rating": i % 5, "author_id": bob.id} for i in range(50)]
        # Bulk Insert (using internal engine for speed, Model.insertMany not exposed?)
        # BaseEngine has insertMany.
        # Let's use loop for simplicity or check if Model has insert_many?
        # Model doesn't expose insert_many explicitly in my code view.
        # Use loop or access engine.
        engine = Post.get_engine()
        await engine.insertMany(Post.get_table_name(), posts_data)
        
        # Paginate: Page 2, size 10 (Posts 10-19)
        page_size = 10
        page = 2
        skip = (page - 1) * page_size
        
        # Sort by title usually string sort: "Post 0", "Post 1", "Post 10"...
        # Let's sort by ID or creation? SQLite rowid is implicit. 
        # But we inserted them in order.
        # Let's simple skip/limit.
        
        paged_posts = await Post.find().skip(skip).limit(page_size).exec()
        print(f"   Fetched {len(paged_posts)} posts for page {page}.")
        assert len(paged_posts) == 10
        print("   [OK] Pagination query")
        
    except Exception as e:
         print(f"[X] Pagination failed: {e}")

    # 8. Benchmark
    print("8. Simple Benchmark...")
    import time
    start = time.time()
    count = 100
    model_instances = [Post(title=f"Bench {i}", author_id=alice.id, rating=5) for i in range(count)]
    # Saving one by one
    for p in model_instances:
        await p.save()
    end = time.time()
    duration = end - start
    print(f"   Inserted {count} records one-by-one in {duration:.4f}s ({count/duration:.1f} ops/s)")
    
    start = time.time()
    # Read 100 times
    for _ in range(count):
        await Post.find().limit(1).exec()
    end = time.time()
    duration = end - start
    print(f"   Read {count} queries in {duration:.4f}s ({count/duration:.1f} ops/s)")

if __name__ == "__main__":
    asyncio.run(verify_complex())
