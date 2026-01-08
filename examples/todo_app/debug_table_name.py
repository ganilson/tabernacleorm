import asyncio
from tabernacleorm import connect, get_connection
from models import User, TodoList, TodoItem
import config

async def debug():
    print(f"DEBUG: TodoList table name from meta: {TodoList._tabernacle_meta['table_name']}")
    print(f"DEBUG: TodoList table name from get_table_name(): {TodoList.get_table_name()}")
    
    connect(config.DATABASE_URL, auto_create=True)
    await get_connection().connect()
    
    engine = get_connection().engine
    # Query sqlite_master to see what tables exist
    tables = await engine.executeRaw("SELECT name FROM sqlite_master WHERE type='table'")
    print(f"DEBUG: Tables in DB: {[t['name'] for t in tables]}")
    
    await get_connection().disconnect()

if __name__ == "__main__":
    asyncio.run(debug())
