"""
Test Find and Modify Operations
Demonstrates findOneAndUpdate, findByIdAndUpdate, findOneAndDelete, findByIdAndDelete
"""

import asyncio
from tabernacleorm import connect, Model, fields


class Product(Model):
    name = fields.StringField(required=True)
    price = fields.FloatField(required=True)
    stock = fields.IntegerField(default=0)
    category = fields.StringField()
    
    class Meta:
        collection = "products"


async def main():
    print("=" * 60)
    print("TabernacleORM - Find and Modify Test")
    print("=" * 60)
    
    # Connect
    db = connect("sqlite:///test_find_modify.db")
    await db.connect()
    
    # Create table
    print("\n📦 Creating table...")
    await Product.createTable()
    
    # Create test data
    print("\n📝 Creating test products...")
    laptop = await Product.create(name="Laptop", price=999.99, stock=10, category="Electronics")
    phone = await Product.create(name="Phone", price=599.99, stock=25, category="Electronics")
    book = await Product.create(name="Python Book", price=39.99, stock=50, category="Books")
    
    print("✅ Test data created!")
    
    # Test 1: findOneAndUpdate (return original)
    print("\n" + "=" * 60)
    print("Test 1: findOneAndUpdate - Return Original")
    print("=" * 60)
    print(f"Before: Laptop price = ${laptop.price}")
    
    original = await Product.findOneAndUpdate(
        {"name": "Laptop"},
        {"$set": {"price": 899.99}},
        new=False  # Return original document
    )
    
    if original:
        print(f"Returned (original): ${original.price}")
    
    updated = await Product.findOne({"name": "Laptop"})
    print(f"After update: ${updated.price}")
    
    # Test 2: findOneAndUpdate (return new)
    print("\n" + "=" * 60)
    print("Test 2: findOneAndUpdate - Return New")
    print("=" * 60)
    print(f"Before: Phone stock = {phone.stock}")
    
    new_doc = await Product.findOneAndUpdate(
        {"name": "Phone"},
        {"$set": {"stock": 30}},
        new=True  # Return updated document
    )
    
    if new_doc:
        print(f"Returned (new): stock = {new_doc.stock}")
    
    # Test 3: findByIdAndUpdate
    print("\n" + "=" * 60)
    print("Test 3: findByIdAndUpdate")
    print("=" * 60)
    print(f"Before: Book price = ${book.price}")
    
    updated_book = await Product.findByIdAndUpdate(
        book.id,
        {"$set": {"price": 34.99}},
        new=True
    )
    
    if updated_book:
        print(f"After: Book price = ${updated_book.price}")
    
    # Test 4: findOneAndUpdate with upsert
    print("\n" + "=" * 60)
    print("Test 4: findOneAndUpdate with Upsert")
    print("=" * 60)
    
    # Try to update non-existent product (will create it)
    tablet = await Product.findOneAndUpdate(
        {"name": "Tablet"},
        {"$set": {"name": "Tablet", "price": 399.99, "stock": 15, "category": "Electronics"}},
        new=True,
        upsert=True
    )
    
    if tablet:
        print(f"Created new product: {tablet.name} - ${tablet.price}")
    
    # Verify it was created
    check = await Product.findOne({"name": "Tablet"})
    print(f"Verification: {check.name if check else 'Not found'}")
    
    # Test 5: findOneAndDelete
    print("\n" + "=" * 60)
    print("Test 5: findOneAndDelete")
    print("=" * 60)
    
    deleted = await Product.findOneAndDelete({"name": "Tablet"})
    if deleted:
        print(f"Deleted: {deleted.name} - ${deleted.price}")
    
    # Verify deletion
    check = await Product.findOne({"name": "Tablet"})
    print(f"After deletion: {'Found' if check else 'Not found'}")
    
    # Test 6: findByIdAndDelete
    print("\n" + "=" * 60)
    print("Test 6: findByIdAndDelete")
    print("=" * 60)
    
    # Create a temporary product
    temp = await Product.create(name="Temp Product", price=9.99, stock=1, category="Test")
    print(f"Created temp product: {temp.name}")
    
    deleted = await Product.findByIdAndDelete(temp.id)
    if deleted:
        print(f"Deleted by ID: {deleted.name}")
    
    # Verify deletion
    check = await Product.findById(temp.id)
    print(f"After deletion: {'Found' if check else 'Not found'}")
    
    # Test 7: Update multiple fields
    print("\n" + "=" * 60)
    print("Test 7: Update Multiple Fields")
    print("=" * 60)
    
    updated = await Product.findOneAndUpdate(
        {"name": "Laptop"},
        {"$set": {"price": 849.99, "stock": 15}},
        new=True
    )
    
    if updated:
        print(f"Updated Laptop: ${updated.price}, Stock: {updated.stock}")
    
    # Display final state
    print("\n" + "=" * 60)
    print("Final Product List:")
    print("=" * 60)
    all_products = await Product.findMany()
    for product in all_products:
        print(f"📦 {product.name}: ${product.price} (Stock: {product.stock})")
    
    print("\n" + "=" * 60)
    print("✅ All find and modify tests completed!")
    print("=" * 60)
    
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
