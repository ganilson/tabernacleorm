# MongoDB Replica Sets Guide

## What are MongoDB Replica Sets?

A **replica set** is a group of MongoDB servers that maintain the same data set, providing:
- **High Availability**: Automatic failover
- **Data Redundancy**: Multiple copies of data
- **Read Scalability**: Distribute reads across secondaries
- **Zero Downtime**: Maintenance without stopping the application

## Architecture

```
┌─────────────────────────────────────────────────┐
│           MongoDB Replica Set (rs0)             │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │ PRIMARY  │───▶│SECONDARY │───▶│SECONDARY │ │
│  │  :27017  │    │  :27018  │    │  :27019  │ │
│  └──────────┘    └──────────┘    └──────────┘ │
│       │               │               │        │
│       │               │               │        │
│    WRITES          READS           READS       │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Configuration in Library Management System

### 1. Environment Variables

```env
# Replica Set Connection
DATABASE_URL=mongodb://localhost:27017,localhost:27018,localhost:27019/library?replicaSet=rs0

# Read Preference (where to read from)
MONGODB_READ_PREFERENCE=secondaryPreferred
# Options: primary, secondary, primaryPreferred, secondaryPreferred, nearest

# Write Concern (acknowledgment level)
MONGODB_WRITE_CONCERN=majority
# Options: 0 (no ack), 1 (acknowledged), majority (majority of nodes)
```

### 2. Connection String Format

```
mongodb://[host1]:[port1],[host2]:[port2],[host3]:[port3]/[database]?replicaSet=[rsName]&[options]
```

**Examples:**

```bash
# Local replica set
mongodb://localhost:27017,localhost:27018,localhost:27019/library?replicaSet=rs0

# Production with authentication
mongodb://user:pass@prod1:27017,prod2:27017,prod3:27017/library?replicaSet=rs0&authSource=admin

# MongoDB Atlas
mongodb+srv://user:pass@cluster.mongodb.net/library?retryWrites=true&w=majority
```

## Read Preferences Explained

### 1. `primary` (default)
- All reads from PRIMARY
- Strongest consistency
- No read scalability

```python
MONGODB_READ_PREFERENCE=primary
```

### 2. `secondary`
- All reads from SECONDARY
- May read stale data
- Maximum read scalability

```python
MONGODB_READ_PREFERENCE=secondary
```

### 3. `secondaryPreferred` (recommended)
- Reads from SECONDARY if available
- Falls back to PRIMARY if no secondary
- Good balance of consistency and performance

```python
MONGODB_READ_PREFERENCE=secondaryPreferred
```

### 4. `primaryPreferred`
- Reads from PRIMARY if available
- Falls back to SECONDARY if primary unavailable
- Good for high consistency needs

```python
MONGODB_READ_PREFERENCE=primaryPreferred
```

### 5. `nearest`
- Reads from nearest node (lowest latency)
- Best for geographically distributed apps

```python
MONGODB_READ_PREFERENCE=nearest
```

## Write Concerns Explained

### 1. `w: 0` - No Acknowledgment
- Fastest writes
- No guarantee of persistence
- Use for non-critical logs

```python
MONGODB_WRITE_CONCERN=0
```

### 2. `w: 1` - Acknowledged (default)
- Write acknowledged by PRIMARY
- Good balance
- Most common setting

```python
MONGODB_WRITE_CONCERN=1
```

### 3. `w: majority` - Majority Acknowledgment
- Write acknowledged by majority of nodes
- Strongest durability
- Slower writes
- Recommended for critical data

```python
MONGODB_WRITE_CONCERN=majority
```

## Setting Up Local Replica Set

### Step 1: Start MongoDB Instances

```bash
# Terminal 1 - Primary
mongod --replSet rs0 --port 27017 --dbpath /data/db1 --bind_ip localhost

# Terminal 2 - Secondary 1
mongod --replSet rs0 --port 27018 --dbpath /data/db2 --bind_ip localhost

# Terminal 3 - Secondary 2
mongod --replSet rs0 --port 27019 --dbpath /data/db3 --bind_ip localhost
```

### Step 2: Initialize Replica Set

```bash
# Connect to one instance
mongo --port 27017

# Initialize
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "localhost:27017" },
    { _id: 1, host: "localhost:27018" },
    { _id: 2, host: "localhost:27019" }
  ]
})

# Check status
rs.status()
```

### Step 3: Configure Library App

```env
DATABASE_URL=mongodb://localhost:27017,localhost:27018,localhost:27019/library?replicaSet=rs0
MONGODB_READ_PREFERENCE=secondaryPreferred
MONGODB_WRITE_CONCERN=majority
```

### Step 4: Run Application

```bash
uvicorn app.main:app --reload
```

## Benefits in Library Management System

### 1. High Availability
```
If PRIMARY fails:
1. Automatic election of new PRIMARY
2. Application continues without interruption
3. No data loss (with w:majority)
```

### 2. Read Scalability
```
Read Operations (GET requests):
- List books → SECONDARY
- Search books → SECONDARY
- Get statistics → SECONDARY

Write Operations (POST/PUT/DELETE):
- Create book → PRIMARY
- Borrow book → PRIMARY
- Return book → PRIMARY
```

### 3. Zero Downtime Maintenance
```
1. Update SECONDARY 1 → Still serving reads
2. Update SECONDARY 2 → Still serving reads
3. Stepdown PRIMARY → New election
4. Update old PRIMARY → Complete
```

## Performance Comparison

### Without Replica Set
```
Concurrent Users: 100
Read Operations: 500 req/s
Write Operations: 100 req/s
Single Point of Failure: YES
```

### With Replica Set (3 nodes)
```
Concurrent Users: 300+
Read Operations: 1500 req/s (3x)
Write Operations: 100 req/s (same)
Single Point of Failure: NO
```

## Monitoring Replica Set

### Check Status
```javascript
// In mongo shell
rs.status()
rs.conf()
rs.printReplicationInfo()
rs.printSecondaryReplicationInfo()
```

### Python Monitoring
```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017,localhost:27018,localhost:27019/?replicaSet=rs0")

# Check replica set status
admin_db = client.admin
status = admin_db.command("replSetGetStatus")
print(f"Replica Set: {status['set']}")
print(f"Members: {len(status['members'])}")

for member in status['members']:
    print(f"  {member['name']}: {member['stateStr']}")
```

## Best Practices

### 1. Use Odd Number of Nodes
- 3 nodes (recommended minimum)
- 5 nodes (for critical systems)
- Prevents split-brain scenarios

### 2. Geographic Distribution
```
Node 1: Data Center A (Primary)
Node 2: Data Center B (Secondary)
Node 3: Data Center C (Secondary)
```

### 3. Read Preference Strategy
```python
# For Library Management:
# - Book searches: secondaryPreferred (high read volume)
# - User loans: primary (consistency critical)
# - Statistics: secondary (eventual consistency OK)
```

### 4. Write Concern Strategy
```python
# Critical operations (loans, returns)
MONGODB_WRITE_CONCERN=majority

# Non-critical (logs, analytics)
MONGODB_WRITE_CONCERN=1
```

## Troubleshooting

### Issue: "not master and slaveOk=false"
**Solution**: Set read preference to allow secondary reads
```env
MONGODB_READ_PREFERENCE=secondaryPreferred
```

### Issue: Slow writes with w:majority
**Solution**: Check network latency between nodes
```bash
# Ping between nodes
ping host2
ping host3
```

### Issue: Replica lag
**Solution**: Monitor replication lag
```javascript
rs.printSecondaryReplicationInfo()
```

## Production Deployment

### MongoDB Atlas (Recommended)
```env
# Automatic replica set management
DATABASE_URL=mongodb+srv://user:pass@cluster.mongodb.net/library?retryWrites=true&w=majority
```

### Self-Hosted
```env
# 3-node replica set with authentication
DATABASE_URL=mongodb://user:pass@prod1:27017,prod2:27017,prod3:27017/library?replicaSet=rs0&authSource=admin&w=majority
```

## Summary

✅ **High Availability**: Automatic failover  
✅ **Read Scalability**: 3x read performance  
✅ **Data Safety**: Multiple copies  
✅ **Zero Downtime**: Rolling updates  
✅ **Geographic Distribution**: Multi-region support  

**Recommended Configuration for Library System:**
- 3-node replica set
- Read Preference: `secondaryPreferred`
- Write Concern: `majority` (for loans), `1` (for logs)
