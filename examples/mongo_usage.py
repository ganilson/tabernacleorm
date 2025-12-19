"""
Example usage of TabernacleORM with MongoDB.

Prerequisites:
    - MongoDB running on localhost:27017
    - pip install motor

Run:
    python examples/mongo_usage.py
"""

import asyncio
from tabernacleorm import (
    connect, 
    disconnect,
    Model,
    EmbeddedModel,
    fields
)

# 1. Define Embedded Models (MongoDB feature)
class Address(EmbeddedModel):
    street = fields.StringField()
    city = fields.StringField()
    zip_code = fields.StringField()

# 2. Define Main Models
class User(Model):
    __collection__ = "users"
    
    name = fields.StringField(required=True)
    email = fields.StringField(unique=True)
    # Embedding a single document
    address = fields.EmbeddedField(Address)
    # Embedding a list of documents (if supported by ArrayField, otherwise we use list of dicts for simple JSON)
    tags = fields.ArrayField(fields.StringField())
    metadata = fields.JSONField()

async def main():
    print("=" * 50)
    print("TabernacleORM - MongoDB Example")
    print("=" * 50)

    # 3. Connect to MongoDB
    print("\nConnecting to MongoDB (localhost:27017)...")
    try:
        # Note: 'tabernacle_example' database will be created automatically
        db = connect("mongodb://localhost:27017/tabernacle_example")
        await db.connect()
        print("Connected!")
    except Exception as e:
        print(f"Failed to connect: {e}")
        print("Please ensure MongoDB is running on localhost:27017")
        return

    # Clean up previous run
    await User.deleteMany({})

    # 4. Create Records with Rich Data
    print("\nCreating users with embedded data...")
    
    # Using the embedded model class
    user_address = Address(
        street="123 Tech Blvd",
        city="Silicon Valley",
        zip_code="94000"
    )

    user = await User.create(
        name="Alice Engineer",
        email="alice@example.com",
        address=user_address,
        tags=["python", "mongodb", "async"],
        metadata={"experience": "senior", "availability": True}
    )
    print(f"Created user: {user.name}")
    print(f"  Address: {user.address.street}, {user.address.city}")
    print(f"  Tags: {user.tags}")

    # 5. Querying
    print("\nQuerying...")
    
    # Find by embedded field (dot notation)
    print("Finding users in 'Silicon Valley'...")
    sv_users = await User.find({"address.city": "Silicon Valley"}).exec()
    for u in sv_users:
        print(f"  - {u.name} ({u.email})")

    # Find by array element
    print("\nFinding users with tag 'rust'...")
    rust_users = await User.find({"tags": "rust"}).exec()
    if not rust_users:
        print("  No users found (expected)")

    # 6. Updates
    print("\nUpdating user...")
    # Modify embedded field
    user.address.street = "456 Innovation Dr"
    # Modify array
    user.tags.append("rust")
    await user.save()
    print("User updated.")

    # Verify update
    updated_user = await User.findById(user.id)
    print(f"New address: {updated_user.address.street}")
    print(f"New tags: {updated_user.tags}")

    # 7. Cleanup
    await disconnect()
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(main())
