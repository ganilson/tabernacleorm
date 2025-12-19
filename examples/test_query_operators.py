"""
Test Query Operators
Demonstrates comparison, logical, and array operators
"""

import asyncio
from tabernacleorm import connect, Model, fields


class User(Model):
    name = fields.StringField(required=True)
    email = fields.StringField(unique=True)
    age = fields.IntegerField()
    status = fields.StringField(default="active")
    tags = fields.JSONField()  # Store as JSON instead of array
    score = fields.FloatField(default=0.0)
    
    class Meta:
        collection = "users"


async def main():
    print("=" * 60)
    print("TabernacleORM - Query Operators Test")
    print("=" * 60)
    
    # Connect
    db = connect("sqlite:///test_operators.db")
    await db.connect()
    
    # Create table
    print("\n📦 Creating table...")
    await User.createTable()
    
    # Create test data
    print("\n📝 Creating test users...")
    await User.create(name="Alice", email="alice@example.com", age=25, status="active", tags=["python", "javascript"], score=95.5)
    await User.create(name="Bob", email="bob@example.com", age=30, status="active", tags=["java", "python"], score=88.0)
    await User.create(name="Charlie", email="charlie@example.com", age=22, status="pending", tags=["javascript", "react"], score=92.3)
    await User.create(name="David", email="david@example.com", age=35, status="inactive", tags=["python", "django"], score=78.5)
    await User.create(name="Eve", email="eve@example.com", age=28, status="active", tags=["rust", "go"], score=91.0)
    await User.create(name="Frank", email="frank@example.com", age=19, status="pending", tags=["python"], score=85.0)
    
    print("✅ Test data created!")
    
    # Test 1: Greater Than (gt)
    print("\n" + "=" * 60)
    print("Test 1: Users with age > 25")
    print("=" * 60)
    users = await User.find().where("age").gt(25).exec()
    for user in users:
        print(f"👤 {user.name} - Age: {user.age}")
    
    # Test 2: Less Than or Equal (lte)
    print("\n" + "=" * 60)
    print("Test 2: Users with age <= 25")
    print("=" * 60)
    users = await User.find().where("age").lte(25).exec()
    for user in users:
        print(f"👤 {user.name} - Age: {user.age}")
    
    # Test 3: Range Query (gte + lte)
    print("\n" + "=" * 60)
    print("Test 3: Users with age between 22 and 30")
    print("=" * 60)
    users = await User.find({"age": {"$gte": 22, "$lte": 30}}).exec()
    for user in users:
        print(f"👤 {user.name} - Age: {user.age}")
    
    # Test 4: IN operator
    print("\n" + "=" * 60)
    print("Test 4: Users with status in ['active', 'pending']")
    print("=" * 60)
    users = await User.find().where("status").in_(["active", "pending"]).exec()
    for user in users:
        print(f"👤 {user.name} - Status: {user.status}")
    
    # Test 5: NOT IN operator
    print("\n" + "=" * 60)
    print("Test 5: Users NOT in inactive status")
    print("=" * 60)
    users = await User.find().where("status").nin(["inactive"]).exec()
    for user in users:
        print(f"👤 {user.name} - Status: {user.status}")
    
    # Test 6: OR operator
    print("\n" + "=" * 60)
    print("Test 6: Users with age < 20 OR age > 30")
    print("=" * 60)
    users = await User.find().or_([
        {"age": {"$lt": 20}},
        {"age": {"$gt": 30}}
    ]).exec()
    for user in users:
        print(f"👤 {user.name} - Age: {user.age}")
    
    # Test 7: AND operator
    print("\n" + "=" * 60)
    print("Test 7: Active users with score > 90")
    print("=" * 60)
    users = await User.find().and_([
        {"status": "active"},
        {"score": {"$gt": 90}}
    ]).exec()
    for user in users:
        print(f"👤 {user.name} - Status: {user.status}, Score: {user.score}")
    
    # Test 8: Regex pattern matching
    print("\n" + "=" * 60)
    print("Test 8: Users with names starting with 'A' or 'B'")
    print("=" * 60)
    users = await User.find().where("name").regex("^[AB]", "i").exec()
    for user in users:
        print(f"👤 {user.name}")
    
    # Test 9: Complex query with chaining
    print("\n" + "=" * 60)
    print("Test 9: Active users, age 20-30, score > 85")
    print("=" * 60)
    users = await User.find({"status": "active", "age": {"$gte": 20, "$lte": 30}, "score": {"$gt": 85}}).exec()
    for user in users:
        print(f"👤 {user.name} - Age: {user.age}, Score: {user.score}")
    
    # Test 10: Array contains (using $in on array field)
    print("\n" + "=" * 60)
    print("Test 10: Users with 'python' tag")
    print("=" * 60)
    # Note: For array contains, we need to query differently
    all_users = await User.findMany()
    python_users = [u for u in all_users if "python" in (u.tags or [])]
    for user in python_users:
        print(f"👤 {user.name} - Tags: {', '.join(user.tags or [])}")
    
    print("\n" + "=" * 60)
    print("✅ All operator tests completed!")
    print("=" * 60)
    
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
