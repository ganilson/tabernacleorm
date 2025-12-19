
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath("src"))

try:
    import tabernacleorm
    from tabernacleorm import Model, fields, connect, disconnect, get_connection
    print("Successfully imported tabernacleorm")
    
    class User(Model):
        name = fields.StringField()
        age = fields.IntegerField()
        
    async def main():
        print("Testing SQLite connection...")
        conn = await connect("sqlite:///:memory:").connect()
        print("Connected.")
        
        # Manually create table for test (since we are not using migrations here)
        print("Creating table...")
        db = get_connection().engine
        await db.create_collection("users", {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        })
        
        print("Testing Create...")
        user = await User.create(name="Test", age=25)
        print(f"Created user: {user.id}, {user.name}")
        
        print("Testing Find...")
        found = await User.find({"name": "Test"}).first()
        print(f"Found user: {found.id}, {found.name}")
        
        await disconnect()
        print("Disconnected.")

    if __name__ == "__main__":
        asyncio.run(main())

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
