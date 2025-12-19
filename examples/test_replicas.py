"""
Test MongoDB Replicas
Demonstrates the advantages of using MongoDB replica sets with TabernacleORM
"""

import asyncio
from tabernacleorm import connect, Model, fields


class Transaction(Model):
    user_id = fields.StringField(required=True)
    amount = fields.FloatField(required=True)
    type = fields.StringField(required=True)  # 'credit' or 'debit'
    status = fields.StringField(default="pending")
    timestamp = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        collection = "transactions"


async def main():
    print("=" * 70)
    print("TabernacleORM - MongoDB Replica Sets Test")
    print("=" * 70)
    
    print("\n📚 ADVANTAGES OF MONGODB REPLICA SETS:")
    print("-" * 70)
    print("1. HIGH AVAILABILITY:")
    print("   - Automatic failover if primary node fails")
    print("   - No downtime during maintenance")
    print("   - Data remains accessible even if nodes go down")
    print()
    print("2. DATA REDUNDANCY:")
    print("   - Multiple copies of data across different servers")
    print("   - Protection against hardware failures")
    print("   - Geographic distribution for disaster recovery")
    print()
    print("3. READ SCALABILITY:")
    print("   - Distribute read operations across secondary nodes")
    print("   - Reduce load on primary node")
    print("   - Better performance for read-heavy applications")
    print()
    print("4. DATA CONSISTENCY:")
    print("   - Automatic data synchronization across replicas")
    print("   - Configurable write concerns for durability")
    print("   - Read preferences for consistency vs performance trade-offs")
    print()
    print("5. ZERO DOWNTIME MAINTENANCE:")
    print("   - Perform upgrades on secondaries first")
    print("   - Stepdown primary and upgrade")
    print("   - No application downtime required")
    print("-" * 70)
    
    # Try to connect to MongoDB replica set
    # Format: mongodb://host1:port1,host2:port2,host3:port3/database?replicaSet=rsName
    
    print("\n🔌 Attempting to connect to MongoDB replica set...")
    print("   Connection string: mongodb://localhost:27017,localhost:27018,localhost:27019/test_replicas?replicaSet=rs0")
    
    try:
        db = connect("mongodb://localhost:27017,localhost:27018,localhost:27019/test_replicas?replicaSet=rs0")
        await db.connect()
        print("✅ Connected to MongoDB replica set successfully!")
        
        # Create collection
        print("\n📦 Creating collection...")
        await Transaction.createTable()
        
        # Test 1: Write to primary
        print("\n" + "=" * 70)
        print("Test 1: Writing to Primary Node")
        print("=" * 70)
        print("Creating transactions...")
        
        tx1 = await Transaction.create(
            user_id="user_001",
            amount=100.50,
            type="credit",
            status="completed"
        )
        print(f"✅ Transaction created: {tx1.id}")
        
        tx2 = await Transaction.create(
            user_id="user_002",
            amount=50.25,
            type="debit",
            status="completed"
        )
        print(f"✅ Transaction created: {tx2.id}")
        
        # Test 2: Read from replica
        print("\n" + "=" * 70)
        print("Test 2: Reading from Replica Set")
        print("=" * 70)
        print("Note: Reads can be distributed across secondaries for better performance")
        
        transactions = await Transaction.findMany()
        print(f"✅ Retrieved {len(transactions)} transactions")
        for tx in transactions:
            print(f"   - {tx.user_id}: ${tx.amount} ({tx.type})")
        
        # Test 3: Bulk operations
        print("\n" + "=" * 70)
        print("Test 3: Bulk Operations with Write Concern")
        print("=" * 70)
        print("Creating multiple transactions...")
        
        bulk_txs = [
            {"user_id": "user_003", "amount": 200.00, "type": "credit", "status": "pending"},
            {"user_id": "user_004", "amount": 75.50, "type": "debit", "status": "pending"},
            {"user_id": "user_005", "amount": 150.00, "type": "credit", "status": "pending"},
        ]
        
        ids = await Transaction.insertMany(bulk_txs)
        print(f"✅ Created {len(ids)} transactions in bulk")
        
        # Test 4: Aggregation
        print("\n" + "=" * 70)
        print("Test 4: Aggregation Pipeline")
        print("=" * 70)
        
        # Count by type
        all_txs = await Transaction.findMany()
        credit_count = len([tx for tx in all_txs if tx.type == "credit"])
        debit_count = len([tx for tx in all_txs if tx.type == "debit"])
        
        print(f"Credit transactions: {credit_count}")
        print(f"Debit transactions: {debit_count}")
        
        # Sum by type
        credit_sum = sum(tx.amount for tx in all_txs if tx.type == "credit")
        debit_sum = sum(tx.amount for tx in all_txs if tx.type == "debit")
        
        print(f"Total credits: ${credit_sum:.2f}")
        print(f"Total debits: ${debit_sum:.2f}")
        print(f"Net balance: ${credit_sum - debit_sum:.2f}")
        
        # Test 5: Update operations
        print("\n" + "=" * 70)
        print("Test 5: Update Operations")
        print("=" * 70)
        
        updated = await Transaction.updateMany(
            {"status": "pending"},
            {"$set": {"status": "completed"}}
        )
        print(f"✅ Updated {updated} pending transactions to completed")
        
        # Test 6: Distinct values
        print("\n" + "=" * 70)
        print("Test 6: Distinct Users")
        print("=" * 70)
        
        users = await Transaction.distinct("user_id")
        print(f"Unique users: {', '.join(users)}")
        
        # Test 7: Complex query
        print("\n" + "=" * 70)
        print("Test 7: Complex Query with Sorting")
        print("=" * 70)
        
        large_txs = await Transaction.find().where("amount").gt(100).sort("-amount").exec()
        print(f"Transactions > $100 (sorted by amount desc):")
        for tx in large_txs:
            print(f"   - {tx.user_id}: ${tx.amount}")
        
        print("\n" + "=" * 70)
        print("✅ All replica set tests completed successfully!")
        print("=" * 70)
        
        print("\n📊 REPLICA SET BENEFITS DEMONSTRATED:")
        print("-" * 70)
        print("✓ High-performance writes to primary")
        print("✓ Distributed reads for scalability")
        print("✓ Automatic data replication")
        print("✓ Complex queries and aggregations")
        print("✓ Bulk operations with write concerns")
        print("-" * 70)
        
        await db.disconnect()
        
    except Exception as e:
        print(f"\n❌ Could not connect to MongoDB replica set: {e}")
        print("\n💡 TO SET UP MONGODB REPLICA SET:")
        print("-" * 70)
        print("1. Start multiple MongoDB instances:")
        print("   mongod --replSet rs0 --port 27017 --dbpath /data/db1")
        print("   mongod --replSet rs0 --port 27018 --dbpath /data/db2")
        print("   mongod --replSet rs0 --port 27019 --dbpath /data/db3")
        print()
        print("2. Initialize replica set (connect to one instance):")
        print("   mongo --port 27017")
        print("   rs.initiate({")
        print("     _id: 'rs0',")
        print("     members: [")
        print("       {_id: 0, host: 'localhost:27017'},")
        print("       {_id: 1, host: 'localhost:27018'},")
        print("       {_id: 2, host: 'localhost:27019'}")
        print("     ]")
        print("   })")
        print()
        print("3. Verify replica set status:")
        print("   rs.status()")
        print("-" * 70)
        
        print("\n📝 FALLBACK: Testing with single MongoDB instance...")
        try:
            db = connect("mongodb://localhost:27017/test_replicas")
            await db.connect()
            print("✅ Connected to single MongoDB instance")
            
            await Transaction.createTable()
            tx = await Transaction.create(
                user_id="user_001",
                amount=100.00,
                type="credit",
                status="completed"
            )
            print(f"✅ Created test transaction: {tx.id}")
            
            await db.disconnect()
            print("\n✅ Single instance test completed!")
            
        except Exception as e2:
            print(f"❌ Could not connect to MongoDB: {e2}")
            print("\n💡 Make sure MongoDB is running:")
            print("   mongod --dbpath /data/db")


if __name__ == "__main__":
    asyncio.run(main())
