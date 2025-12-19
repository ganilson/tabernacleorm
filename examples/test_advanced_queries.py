"""
Test Advanced Queries
Demonstrates distinct, exists, countDocuments, lean, and complex chaining
"""

import asyncio
from tabernacleorm import connect, Model, fields


class Order(Model):
    customer_name = fields.StringField(required=True)
    product = fields.StringField(required=True)
    quantity = fields.IntegerField(default=1)
    status = fields.StringField(default="pending")
    total = fields.FloatField()
    
    class Meta:
        collection = "orders"


async def main():
    print("=" * 60)
    print("TabernacleORM - Advanced Queries Test")
    print("=" * 60)
    
    # Connect
    db = connect("sqlite:///test_advanced.db")
    await db.connect()
    
    # Create table
    print("\n📦 Creating table...")
    await Order.createTable()
    
    # Create test data
    print("\n📝 Creating test orders...")
    await Order.create(customer_name="Alice", product="Laptop", quantity=1, status="completed", total=999.99)
    await Order.create(customer_name="Bob", product="Phone", quantity=2, status="pending", total=1199.98)
    await Order.create(customer_name="Alice", product="Mouse", quantity=3, status="completed", total=89.97)
    await Order.create(customer_name="Charlie", product="Keyboard", quantity=1, status="shipped", total=79.99)
    await Order.create(customer_name="Bob", product="Monitor", quantity=1, status="completed", total=299.99)
    await Order.create(customer_name="Alice", product="Laptop", quantity=1, status="pending", total=999.99)
    await Order.create(customer_name="David", product="Phone", quantity=1, status="cancelled", total=599.99)
    
    print("✅ Test data created!")
    
    # Test 1: exists() - Check if order exists
    print("\n" + "=" * 60)
    print("Test 1: exists() - Check if pending orders exist")
    print("=" * 60)
    
    exists_id = await Order.find({"status": "pending"}).exists()
    print(f"Pending orders exist: {bool(exists_id)}")
    if exists_id:
        print(f"First pending order ID: {exists_id}")
    
    # Test 2: exists() - Non-existent
    print("\n" + "=" * 60)
    print("Test 2: exists() - Check for non-existent status")
    print("=" * 60)
    
    exists_id = await Order.exists({"status": "refunded"})
    print(f"Refunded orders exist: {bool(exists_id)}")
    
    # Test 3: countDocuments()
    print("\n" + "=" * 60)
    print("Test 3: countDocuments() - Count by status")
    print("=" * 60)
    
    total = await Order.countDocuments()
    print(f"Total orders: {total}")
    
    completed = await Order.countDocuments({"status": "completed"})
    print(f"Completed orders: {completed}")
    
    pending = await Order.countDocuments({"status": "pending"})
    print(f"Pending orders: {pending}")
    
    # Test 4: distinct() - Get unique values
    print("\n" + "=" * 60)
    print("Test 4: distinct() - Get unique customers")
    print("=" * 60)
    
    customers = await Order.distinct("customer_name")
    print(f"Unique customers: {', '.join(customers)}")
    
    # Test 5: distinct() with query
    print("\n" + "=" * 60)
    print("Test 5: distinct() - Unique products in completed orders")
    print("=" * 60)
    
    products = await Order.distinct("product", {"status": "completed"})
    print(f"Products in completed orders: {', '.join(products)}")
    
    # Test 6: distinct() on status
    print("\n" + "=" * 60)
    print("Test 6: distinct() - All order statuses")
    print("=" * 60)
    
    statuses = await Order.distinct("status")
    print(f"Order statuses: {', '.join(statuses)}")
    
    # Test 7: lean() - Return plain dicts
    print("\n" + "=" * 60)
    print("Test 7: lean() - Get orders as plain dicts")
    print("=" * 60)
    
    orders = await Order.find({"status": "completed"}).lean().exec()
    print(f"Type of result: {type(orders[0]) if orders else 'empty'}")
    for order in orders[:2]:  # Show first 2
        print(f"📋 {order}")
    
    # Test 8: Complex chaining
    print("\n" + "=" * 60)
    print("Test 8: Complex Query Chain")
    print("=" * 60)
    print("Find: status in ['completed', 'shipped'], total > 100, sort by -total, limit 3")
    
    orders = await Order.find().where("status").in_(["completed", "shipped"]).where("total").gt(100).sort("-total").limit(3).exec()
    
    for order in orders:
        print(f"📦 {order.customer_name} - {order.product}: ${order.total} ({order.status})")
    
    # Test 9: Count with complex query
    print("\n" + "=" * 60)
    print("Test 9: Count with filters")
    print("=" * 60)
    
    count = await Order.find({"customer_name": "Alice"}).count()
    print(f"Alice's orders: {count}")
    
    count = await Order.find().where("total").gte(500).count()
    print(f"Orders >= $500: {count}")
    
    # Test 10: Aggregation-like query
    print("\n" + "=" * 60)
    print("Test 10: Customer Order Summary")
    print("=" * 60)
    
    customers = await Order.distinct("customer_name")
    for customer in customers:
        orders = await Order.find({"customer_name": customer}).exec()
        total_spent = sum(o.total for o in orders)
        order_count = len(orders)
        print(f"👤 {customer}: {order_count} orders, Total: ${total_spent:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ All advanced query tests completed!")
    print("=" * 60)
    
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
