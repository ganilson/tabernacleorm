"""
Database-Specific Examples: MongoDB
Demonstrates MongoDB-specific features and optimizations
"""

import asyncio
from datetime import datetime
from tabernacleorm import connect, Model, fields


# Models optimized for MongoDB
class User(Model):
    username = fields.StringField(required=True, unique=True)
    email = fields.StringField(required=True, unique=True)
    profile = fields.JSONField()  # Embedded document
    preferences = fields.JSONField()
    tags = fields.JSONField()  # Array of strings
    created_at = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        collection = "users"


class Event(Model):
    name = fields.StringField(required=True)
    user_id = fields.ForeignKey(User)
    event_type = fields.StringField()
    metadata = fields.JSONField()  # Flexible schema
    timestamp = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        collection = "events"


async def main():
    print("=" * 60)
    print("MongoDB-Specific Features")
    print("=" * 60)
    
    # Connect to MongoDB
    try:
        db = connect("mongodb://localhost:27017/tabernacle_mongo")
        await db.connect()
        print("Connected to MongoDB")
    except Exception as e:
        print(f"Could not connect to MongoDB: {e}")
        print("Make sure MongoDB is running: mongod")
        return
    
    # Create collections
    await User.createTable()
    await Event.createTable()
    
    # Test 1: Embedded Documents
    print("\n" + "=" * 60)
    print("Test 1: Embedded Documents (JSON Fields)")
    print("=" * 60)
    
    user = await User.create(
        username="john_doe",
        email="john@example.com",
        profile={
            "first_name": "John",
            "last_name": "Doe",
            "age": 30,
            "address": {
                "street": "123 Main St",
                "city": "New York",
                "country": "USA"
            }
        },
        preferences={
            "theme": "dark",
            "language": "en",
            "notifications": True
        },
        tags=["developer", "python", "mongodb"]
    )
    
    print(f"Created user: {user.username}")
    print(f"Profile: {user.profile}")
    print(f"Tags: {user.tags}")
    
    # Test 2: Flexible Schema
    print("\n" + "=" * 60)
    print("Test 2: Flexible Schema with Metadata")
    print("=" * 60)
    
    events = [
        {
            "name": "page_view",
            "user_id": user.id,
            "event_type": "navigation",
            "metadata": {"page": "/home", "duration": 5.2}
        },
        {
            "name": "button_click",
            "user_id": user.id,
            "event_type": "interaction",
            "metadata": {"button_id": "submit", "x": 100, "y": 200}
        },
        {
            "name": "purchase",
            "user_id": user.id,
            "event_type": "transaction",
            "metadata": {
                "product_id": "ABC123",
                "amount": 99.99,
                "currency": "USD",
                "payment_method": "credit_card"
            }
        }
    ]
    
    for event_data in events:
        event = await Event.create(**event_data)
        print(f"Created event: {event.name} - {event.metadata}")
    
    # Test 3: Array Queries
    print("\n" + "=" * 60)
    print("Test 3: Querying Arrays")
    print("=" * 60)
    
    # Find users with specific tag
    all_users = await User.findMany()
    python_users = [u for u in all_users if "python" in (u.tags or [])]
    print(f"Users with 'python' tag: {[u.username for u in python_users]}")
    
    # Test 4: Nested Field Queries
    print("\n" + "=" * 60)
    print("Test 4: Querying Nested Fields")
    print("=" * 60)
    
    # In MongoDB, you can query nested fields with dot notation
    # For now, we fetch and filter in Python
    all_users = await User.findMany()
    ny_users = [u for u in all_users if u.profile.get("address", {}).get("city") == "New York"]
    print(f"Users in New York: {[u.username for u in ny_users]}")
    
    # Test 5: Aggregation
    print("\n" + "=" * 60)
    print("Test 5: Event Aggregation")
    print("=" * 60)
    
    all_events = await Event.findMany()
    
    # Group by event type
    event_counts = {}
    for event in all_events:
        event_type = event.event_type
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
    
    print("Events by type:")
    for event_type, count in event_counts.items():
        print(f"  {event_type}: {count}")
    
    # Test 6: Text Search Simulation
    print("\n" + "=" * 60)
    print("Test 6: Text Search")
    print("=" * 60)
    
    search_term = "john"
    users = await User.findMany()
    matching_users = [
        u for u in users
        if search_term.lower() in u.username.lower() or
           search_term.lower() in u.email.lower()
    ]
    
    print(f"Users matching '{search_term}': {[u.username for u in matching_users]}")
    
    # Test 7: Bulk Operations
    print("\n" + "=" * 60)
    print("Test 7: Bulk Insert")
    print("=" * 60)
    
    bulk_users = [
        {"username": f"user_{i}", "email": f"user{i}@example.com", "tags": ["bulk", "test"]}
        for i in range(5)
    ]
    
    ids = await User.insertMany(bulk_users)
    print(f"Bulk inserted {len(ids)} users")
    
    # Test 8: Update with Operators
    print("\n" + "=" * 60)
    print("Test 8: Update Operations")
    print("=" * 60)
    
    # Update user preferences
    updated = await User.updateMany(
        {"username": "john_doe"},
        {"$set": {"preferences.theme": "light"}}
    )
    print(f"Updated {updated} users")
    
    # Verify update
    john = await User.findOne({"username": "john_doe"})
    print(f"John's theme: {john.preferences.get('theme')}")
    
    # Test 9: Distinct Values
    print("\n" + "=" * 60)
    print("Test 9: Distinct Event Types")
    print("=" * 60)
    
    event_types = await Event.distinct("event_type")
    print(f"Distinct event types: {event_types}")
    
    # Test 10: Count and Exists
    print("\n" + "=" * 60)
    print("Test 10: Count and Exists")
    print("=" * 60)
    
    total_users = await User.count()
    total_events = await Event.count()
    
    print(f"Total users: {total_users}")
    print(f"Total events: {total_events}")
    
    has_purchases = await Event.exists({"event_type": "transaction"})
    print(f"Has purchase events: {bool(has_purchases)}")
    
    print("\n" + "=" * 60)
    print("MongoDB examples completed!")
    print("=" * 60)
    
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
