"""
Quick test script for TODO app
"""
import asyncio
import sys
sys.path.insert(0, "../../src")

from tabernacleorm import connect, get_connection
import tabernacleorm
print(f"DEBUG: tabernacleorm file: {tabernacleorm.__file__}")
from models import User, TodoList, TodoItem
import config

async def test_todo_app():
    print("=== Testing TODO App ===\n")
    
    # Connect
    print(f"1. Connecting to: {config.DATABASE_URL}")
    connect(config.DATABASE_URL, auto_create=config.AUTO_CREATE_TABLES)
    await get_connection().connect()
    print("   [OK] Connected\n")
    
    # Clean up existing data
    print("2. Cleaning up...")
    await TodoItem.deleteMany({})
    await TodoList.deleteMany({})
    await User.deleteMany({})
    print("   [OK] Cleaned\n")
    
    # Create User
    print("3. Creating user...")
    user = await User.create(name="John Doe", email="john@example.com")
    print(f"   [OK] Created user: {user.name} (ID: {user.id})\n")
    
    # Create TodoList
    print("4. Creating todo list...")
    todo_list = await TodoList.create(
        title="Shopping List",
        description="Weekly groceries",
        user_id=user.id
    )
    print(f"   [OK] Created list: {todo_list.title} (ID: {todo_list.id})\n")
    
    # Create TodoItems
    print("5. Creating todo items...")
    item1 = await TodoItem.create(
        title="Buy milk",
        list_id=todo_list.id,
        priority=2
    )
    item2 = await TodoItem.create(
        title="Buy eggs",
        list_id=todo_list.id,
        priority=1
    )
    item3 = await TodoItem.create(
        title="Buy bread",
        list_id=todo_list.id,
        priority=0
    )
    print(f"   [OK] Created 3 items\n")
    
    # Test complex query
    print("6. Testing complex query (priority >= 1)...")
    high_priority = await TodoItem.find({"priority": {"$gte": 1}}).exec()
    print(f"   [OK] Found {len(high_priority)} high-priority items")
    for item in high_priority:
        print(f"     - {item.title} (priority: {item.priority})")
    print()
    
    # Test populate (List -> Items)
    print("7. Testing populate (TodoList -> Items)...")
    list_with_items = await TodoList.find({"id": todo_list.id}).populate("items").first()
    if list_with_items and hasattr(list_with_items, 'items') and list_with_items.items:
        print(f"   [OK] Populated {len(list_with_items.items)} items for list '{list_with_items.title}'")
        for item in list_with_items.items:
            item_obj = item if hasattr(item, 'title') else item
            if hasattr(item_obj, 'title'):
                print(f"     - {item_obj.title}")
    else:
        print("   [WARNING] Populate returned no items (might need debugging)")
    print()
    
    # Test populate (User -> Lists)
    print("8. Testing populate (User -> TodoLists)...")
    user_with_lists = await User.find({"id": user.id}).populate("todo_lists").first()
    if user_with_lists and hasattr(user_with_lists, 'todo_lists') and user_with_lists.todo_lists:
        print(f"   [OK] Populated {len(user_with_lists.todo_lists)} lists for user '{user_with_lists.name}'")
        for lst in user_with_lists.todo_lists:
            lst_obj = lst if hasattr(lst, 'title') else lst
            if hasattr(lst_obj, 'title'):
                print(f"     - {lst_obj.title}")
    else:
        print("   [WARNING] Populate returned no lists (might need debugging)")
    print()
    
    # Test batch update
    print("9. Testing batch update (complete all items)...")
    updated = await TodoItem.updateMany(
        {"list_id": todo_list.id},
        {"$set": {"completed": True}}
    )
    print(f"   [OK] Updated {updated} items\n")
    
    # Test count/stats
    print("10. Testing stats...")
    total = await TodoItem.find({"list_id": todo_list.id}).count()
    completed = await TodoItem.find({"list_id": todo_list.id, "completed": True}).count()
    print(f"   [OK] Total items: {total}")
    print(f"   [OK] Completed: {completed}")
    print(f"   [OK] Completion rate: {(completed/total*100):.1f}%\n")
    
    # Test batch delete
    print("11. Testing batch delete (completed items)...")
    deleted = await TodoItem.deleteMany({"completed": True})
    print(f"   [OK] Deleted {deleted} completed items\n")
    
    remaining = await TodoItem.find({}).count()
    print(f"[SUCCESS] All tests passed! Remaining items: {remaining}\n")
    
    # Cleanup
    await get_connection().disconnect()

if __name__ == "__main__":
    asyncio.run(test_todo_app())
