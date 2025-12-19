
"""
TabernacleORM - MongoDB Replica Set & Read/Write Splitting Example.

This example demonstrates how to configure TabernacleORM to use different
MongoDB nodes for Write operations (Primary) and Read operations (Secondaries).

PREREQUISITES:
You need a MongoDB Replica Set running locally or accessible.
For this example, we assume:
- Primary: localhost:27017
- Secondary 1: localhost:27018
- Secondary 2: localhost:27019

If you only have one mongo instance, you can point all to 27017 to simulate tests.
"""

import asyncio
import random
from tabernacleorm import connect, Model, fields

# 1. Define Model
class LogEntry(Model):
    level = fields.StringField(required=True)
    message = fields.StringField(required=True)
    timestamp = fields.DateTimeField(auto_now_add=True)
    source_node = fields.StringField()

    class Meta:
        collection = "system_logs"

async def main():
    print("Initializing Advanced MongoDB Configuration...")
    
    # 2. Advanced Connection Configuration
    # We define explicit Write and Read configurations.
    # TabernacleORM will route .save/.create/delete to 'write' engine
    # and .find/.findOne to 'read' engines (round-robin).
    
    # Note: In a real Replica Set using standard drivers, the driver often handles 
    # reading from secondaries if you pass 'readPreference=secondary'.
    # However, TabernacleORM allows explicit application-side splitting 
    # which is useful for specialized architectures or distinct clusters.
    
    db = connect(
        # Base config (defaults)
        url="mongodb://localhost:27017/logs_db",
        
        # Write Configuration (Primary)
        write={
             "url": "mongodb://localhost:27017/logs_db",
             "pool_size": 10
        },
        
        # Read Configuration (List of Secondaries)
        read=[
            {"url": "mongodb://localhost:27017/logs_db", "pool_size": 5}, # Using 27017 for demo if others down
            # {"url": "mongodb://localhost:27018/logs_db", "pool_size": 5},
            # {"url": "mongodb://localhost:27019/logs_db", "pool_size": 5}
        ]
    )
    await db.connect()
    print("Connected to Primary and Read Replicas.")

    # 3. Simulate High Volume Writes (Primary)
    print("\n--- Writing Data (to Primary) ---")
    levels = ["INFO", "WARN", "ERROR"]
    for i in range(5):
        log = await LogEntry.create(
            level=random.choice(levels),
            message=f"System event #{i}",
            source_node="app-server-01"
        )
        print(f"Written Log ID: {log.id}")

    # 4. Simulate Reads (Load Balanced)
    print("\n--- Reading Data (Round-Robin from Secondaries) ---")
    # To verify load balancing, we'd need to check logs on the mongo instances.
    # Internally, TabernacleORM is rotating engines.
    
    for i in range(5):
        # This calls Connection.get_read_engine() internally
        logs = await LogEntry.find({"message": f"System event #{i}"}).exec()
        if logs:
            print(f"Read Log: {logs[0].message} (via Read Engine)")
        else:
            print(f"Log #{i} not found (might be replication lag if real RS)")

    # 5. Manual Engine Selection (Optional)
    # You can force usage of write engine for critical reads (read-your-writes)
    print("\n--- Critical Read (Force Primary) ---")
    # This feature requires access to underlying engine or context manager (future feature)
    # For now, default find() uses read replicas if configured.
    
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
