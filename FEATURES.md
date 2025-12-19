# TabernacleORM - Comprehensive Feature Documentation

## New Mongoose-Inspired Features (v2.1.0)

### Enhanced Populate Functionality

TabernacleORM now supports advanced populate features similar to Mongoose:

#### Simple Populate
```python
# Populate a single reference
posts = await Post.find().populate("author_id").exec()
for post in posts:
    print(post.author_id.name)  # Access populated author
```

#### Populate with Field Selection
```python
# Only populate specific fields
posts = await Post.find().populate("author_id", select=["name", "email"]).exec()
```

#### Populate with Match Filter
```python
# Only populate authors matching criteria
posts = await Post.find().populate(
    "author_id",
    match={"department_id": dept_id}
).exec()
```

#### Populate with Options
```python
# Control sorting and limiting of populated documents
comments = await Comment.find().populate(
    "post_id",
    options={"sort": "-views", "limit": 5}
).exec()
```

#### Nested Populate
```python
# Populate multiple levels (author -> department)
posts = await Post.find().populate("author_id").exec()
# Then manually populate nested (full nested support coming soon)
for post in posts:
    if hasattr(post.author_id, 'department_id'):
        dept = await Department.findById(post.author_id.department_id)
        post.author_id.department_id = dept
```

#### Multiple Field Populate
```python
# Populate multiple fields
posts = await Post.find().populate("author_id").populate("category_id").exec()
```

---

### New Model Methods

#### findOneAndUpdate()
Find and update a document atomically:
```python
# Return original document
original = await Product.findOneAndUpdate(
    {"name": "Laptop"},
    {"$set": {"price": 899.99}},
    new=False
)

# Return updated document
updated = await Product.findOneAndUpdate(
    {"name": "Laptop"},
    {"$set": {"price": 899.99}},
    new=True
)

# Upsert (create if doesn't exist)
doc = await Product.findOneAndUpdate(
    {"name": "Tablet"},
    {"$set": {"name": "Tablet", "price": 399.99}},
    upsert=True,
    new=True
)
```

#### findByIdAndUpdate()
Update by ID:
```python
updated = await Product.findByIdAndUpdate(
    product_id,
    {"$set": {"stock": 30}},
    new=True
)
```

#### findOneAndDelete()
Find and delete atomically:
```python
deleted = await Product.findOneAndDelete({"name": "OldProduct"})
if deleted:
    print(f"Deleted: {deleted.name}")
```

#### findByIdAndDelete()
Delete by ID:
```python
deleted = await Product.findByIdAndDelete(product_id)
```

#### exists()
Check if documents exist:
```python
exists_id = await Order.exists({"status": "pending"})
if exists_id:
    print(f"Pending order found: {exists_id}")
```

#### countDocuments()
Count documents (Mongoose alias):
```python
total = await Product.countDocuments()
active = await Product.countDocuments({"status": "active"})
```

#### distinct()
Get unique values:
```python
categories = await Product.distinct("category")
customers = await Order.distinct("customer_name", {"status": "completed"})
```

#### where()
Start a chainable query:
```python
users = await User.where("age").gt(18).exec()
```

---

### New QuerySet Methods

#### Comparison Operators

```python
# Greater than
users = await User.find().where("age").gt(18).exec()

# Greater than or equal
users = await User.find().where("age").gte(21).exec()

# Less than
users = await User.find().where("age").lt(65).exec()

# Less than or equal
users = await User.find().where("age").lte(30).exec()

# Chaining comparisons
users = await User.find().where("age").gte(18).where("age").lte(65).exec()
```

#### Array Operators

```python
# IN operator
users = await User.find().where("status").in_(["active", "pending"]).exec()

# NOT IN operator
users = await User.find().where("status").nin(["banned", "deleted"]).exec()
```

#### Logical Operators

```python
# OR query
users = await User.find().or_([
    {"age": {"$lt": 18}},
    {"age": {"$gt": 65}}
]).exec()

# AND query (explicit)
users = await User.find().and_([
    {"status": "active"},
    {"score": {"$gt": 90}}
]).exec()

# NOR query (none should match)
users = await User.find().nor([
    {"status": "banned"},
    {"status": "deleted"}
]).exec()
```

#### Pattern Matching

```python
# Regex search
users = await User.find().where("name").regex("^John", "i").exec()  # Case-insensitive
```

#### Performance Optimization

```python
# Lean mode - return plain dicts instead of Model instances
orders = await Order.find().lean().exec()
# Result: list of dicts instead of Model objects (faster)
```

#### Query Utilities

```python
# Check if query has results
exists = await User.find({"status": "active"}).exists()

# Get distinct values from query results
statuses = await Order.find({"customer": "Alice"}).distinct("status")
```

---

### Complex Query Examples

#### Multi-condition Filtering
```python
# Find active users aged 20-30 with score > 85
users = await User.find({
    "status": "active",
    "age": {"$gte": 20, "$lte": 30},
    "score": {"$gt": 85}
}).exec()
```

#### Chained Query Building
```python
# Build complex queries step by step
query = User.find()
query = query.where("status").in_(["active", "premium"])
query = query.where("age").gte(18)
query = query.sort("-created_at")
query = query.limit(10)
users = await query.exec()
```

#### Pagination
```python
# Offset-based pagination
page_size = 20
page_num = 2
skip = (page_num - 1) * page_size

products = await Product.find().sort("-created_at").skip(skip).limit(page_size).exec()
```

#### Cursor-based Pagination
```python
# First page
first_page = await Article.find().sort("id").limit(10).exec()

# Next page (using last ID from previous page)
if first_page:
    last_id = first_page[-1].id
    next_page = await Article.find({"id": {"$gt": last_id}}).sort("id").limit(10).exec()
```

---

### MongoDB Replica Sets

TabernacleORM supports MongoDB replica sets for high availability and scalability:

```python
# Connect to replica set
db = connect("mongodb://host1:27017,host2:27018,host3:27019/mydb?replicaSet=rs0")
await db.connect()
```

#### Advantages of Replica Sets:

1. **High Availability**: Automatic failover if primary node fails
2. **Data Redundancy**: Multiple copies across different servers
3. **Read Scalability**: Distribute reads across secondary nodes
4. **Zero Downtime**: Maintenance without application downtime
5. **Geographic Distribution**: Data centers in different locations

See `examples/test_replicas.py` for a complete demonstration.

---

### Example Files

The `examples/` directory contains comprehensive tests for all features:

- `test_populate.py` - All populate features (simple, nested, select, match, options)
- `test_query_operators.py` - Comparison and logical operators
- `test_find_and_modify.py` - findOneAndUpdate, findByIdAndUpdate, etc.
- `test_advanced_queries.py` - exists, distinct, countDocuments, lean
- `test_sorting_pagination.py` - Sorting and pagination strategies
- `test_hooks_validation.py` - Pre/post hooks and custom validation
- `test_replicas.py` - MongoDB replica set advantages

---

### Migration from v2.0 to v2.1

All new features are backward compatible. Existing code will continue to work without changes.

#### New Methods Available:
- Model: `findOneAndUpdate`, `findByIdAndUpdate`, `findOneAndDelete`, `findByIdAndDelete`, `exists`, `countDocuments`, `distinct`, `where`
- QuerySet: `where`, `or_`, `and_`, `nor`, `gt`, `gte`, `lt`, `lte`, `in_`, `nin`, `regex`, `lean`, `exists`, `distinct`

#### Enhanced Features:
- Populate now supports: `select`, `match`, `options`, nested paths, multiple fields

---

### Performance Tips

1. **Use `lean()` for read-only queries**: Returns plain dicts, ~30% faster
2. **Use `select()` to limit fields**: Reduces data transfer
3. **Use indexes**: Create indexes on frequently queried fields
4. **Use `countDocuments()` instead of loading all docs**: More efficient counting
5. **Use cursor-based pagination**: Better performance than offset pagination for large datasets

---

### Complete API Reference

For the complete API documentation, see the main [README.md](../README.md).

For migration guides and tutorials, visit our [documentation](https://github.com/ganilson/tabernacleorm#readme).
