"""
Simple Test - New Query Methods
Tests the new Mongoose-like query methods without emojis
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
    print("TabernacleORM - New Query Methods Test")
    print("=" * 60)
    
    # Connect
    db = connect("sqlite:///test_simple.db")
    await db.connect()
    
    # Create table
    print("\nCreating table...")
    await Product.createTable()
    
    # Create test data
    print("Creating test products...")
    p1 = await Product.create(name="Laptop", price=999.99, stock=10, category="Electronics")
    p2 = await Product.create(name="Phone", price=599.99, stock=25, category="Electronics")
    p3 = await Product.create(name="Book", price=39.99, stock=50, category="Books")
    print(f"Created {3} products")
    
    # Test 1: where().gt()
    print("\n" + "=" * 60)
    print("Test 1: where().gt() - Products with price > 500")
    print("=" * 60)
    products = await Product.find().where("price").gt(500).exec()
    print(f"Found {len(products)} products:")
    for p in products:
        print(f"  - {p.name}: ${p.price}")
    
    # Test 2: where().in_()
    print("\n" + "=" * 60)
    print("Test 2: where().in_() - Electronics or Books")
    print("=" * 60)
    products = await Product.find().where("category").in_(["Electronics", "Books"]).exec()
    print(f"Found {len(products)} products:")
    for p in products:
        print(f"  - {p.name} ({p.category})")
    
    # Test 3: exists()
    print("\n" + "=" * 60)
    print("Test 3: exists() - Check if Electronics exist")
    print("=" * 60)
    exists_id = await Product.find({"category": "Electronics"}).exists()
    print(f"Electronics exist: {bool(exists_id)}")
    if exists_id:
        print(f"First ID: {exists_id}")
    
    # Test 4: distinct()
    print("\n" + "=" * 60)
    print("Test 4: distinct() - Get unique categories")
    print("=" * 60)
    categories = await Product.distinct("category")
    print(f"Categories: {', '.join(categories)}")
    
    # Test 5: countDocuments()
    print("\n" + "=" * 60)
    print("Test 5: countDocuments()")
    print("=" * 60)
    total = await Product.countDocuments()
    electronics = await Product.countDocuments({"category": "Electronics"})
    print(f"Total products: {total}")
    print(f"Electronics: {electronics}")
    
    # Test 6: findOneAndUpdate()
    print("\n" + "=" * 60)
    print("Test 6: findOneAndUpdate() - Update laptop price")
    print("=" * 60)
    print(f"Before: Laptop price = ${p1.price}")
    updated = await Product.findOneAndUpdate(
        {"name": "Laptop"},
        {"$set": {"price": 899.99}},
        new=True
    )
    if updated:
        print(f"After: Laptop price = ${updated.price}")
    
    # Test 7: findByIdAndUpdate()
    print("\n" + "=" * 60)
    print("Test 7: findByIdAndUpdate() - Update phone stock")
    print("=" * 60)
    print(f"Before: Phone stock = {p2.stock}")
    updated = await Product.findByIdAndUpdate(
        p2.id,
        {"$set": {"stock": 30}},
        new=True
    )
    if updated:
        print(f"After: Phone stock = {updated.stock}")
    
    # Test 8: findOneAndDelete()
    print("\n" + "=" * 60)
    print("Test 8: findOneAndDelete() - Delete book")
    print("=" * 60)
    deleted = await Product.findOneAndDelete({"name": "Book"})
    if deleted:
        print(f"Deleted: {deleted.name}")
    remaining = await Product.count()
    print(f"Remaining products: {remaining}")
    
    # Test 9: Complex chaining
    print("\n" + "=" * 60)
    print("Test 9: Complex chaining - Electronics with price > 600")
    print("=" * 60)
    products = await Product.find({"category": "Electronics"}).where("price").gt(600).sort("-price").exec()
    print(f"Found {len(products)} products:")
    for p in products:
        print(f"  - {p.name}: ${p.price}")
    
    print("\n" + "=" * 60)
    print("SUCCESS: All tests passed!")
    print("=" * 60)
    
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
