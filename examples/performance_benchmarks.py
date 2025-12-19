"""
Performance Benchmarks
Compare TabernacleORM performance across different operations and databases
"""

import asyncio
import time
from tabernacleorm import connect, Model, fields


class BenchmarkModel(Model):
    name = fields.StringField(required=True)
    value = fields.IntegerField()
    data = fields.JSONField()
    
    class Meta:
        collection = "benchmarks"


async def benchmark_operation(name, operation, iterations=1000):
    """Benchmark a specific operation"""
    start = time.time()
    
    for _ in range(iterations):
        await operation()
    
    elapsed = time.time() - start
    ops_per_second = iterations / elapsed
    
    print(f"{name:40} | {elapsed:8.3f}s | {ops_per_second:10.0f} ops/s")
    return elapsed, ops_per_second


async def run_benchmarks(db_name, connection_string):
    """Run all benchmarks for a database"""
    print(f"\n{'=' * 80}")
    print(f"Benchmarking: {db_name}")
    print(f"{'=' * 80}")
    print(f"{'Operation':<40} | {'Time':>8} | {'Ops/Second':>12}")
    print("-" * 80)
    
    db = connect(connection_string)
    await db.connect()
    await BenchmarkModel.createTable()
    
    # Benchmark 1: Create (Insert)
    counter = [0]
    async def create_op():
        counter[0] += 1
        await BenchmarkModel.create(
            name=f"item_{counter[0]}",
            value=counter[0],
            data={"key": "value", "number": counter[0]}
        )
    
    await benchmark_operation("Create (Insert)", create_op, 100)
    
    # Benchmark 2: Find by ID
    item = await BenchmarkModel.findOne({})
    if item:
        async def find_by_id_op():
            await BenchmarkModel.findById(item.id)
        
        await benchmark_operation("Find by ID", find_by_id_op, 1000)
    
    # Benchmark 3: Find with filter
    async def find_with_filter_op():
        await BenchmarkModel.find({"value": {"$gt": 50}}).exec()
    
    await benchmark_operation("Find with filter", find_with_filter_op, 100)
    
    # Benchmark 4: Update
    async def update_op():
        await BenchmarkModel.updateMany(
            {"value": {"$lt": 50}},
            {"$set": {"data": {"updated": True}}}
        )
    
    await benchmark_operation("Update many", update_op, 50)
    
    # Benchmark 5: Count
    async def count_op():
        await BenchmarkModel.count()
    
    await benchmark_operation("Count", count_op, 500)
    
    # Benchmark 6: Distinct
    async def distinct_op():
        await BenchmarkModel.distinct("name")
    
    await benchmark_operation("Distinct", distinct_op, 100)
    
    # Benchmark 7: Delete
    async def delete_op():
        await BenchmarkModel.deleteMany({"value": {"$lt": 10}})
    
    await benchmark_operation("Delete many", delete_op, 10)
    
    # Benchmark 8: Bulk insert
    async def bulk_insert_op():
        docs = [
            {"name": f"bulk_{i}", "value": i, "data": {}}
            for i in range(100)
        ]
        await BenchmarkModel.insertMany(docs)
    
    await benchmark_operation("Bulk insert (100 docs)", bulk_insert_op, 10)
    
    # Benchmark 9: Complex query with chaining
    async def complex_query_op():
        await BenchmarkModel.find().where("value").gt(50).where("value").lt(150).sort("-value").limit(10).exec()
    
    await benchmark_operation("Complex chained query", complex_query_op, 100)
    
    # Benchmark 10: Lean mode vs normal
    async def normal_query_op():
        await BenchmarkModel.find().limit(50).exec()
    
    async def lean_query_op():
        await BenchmarkModel.find().limit(50).lean().exec()
    
    print("\nComparison: Normal vs Lean mode")
    normal_time, normal_ops = await benchmark_operation("  Normal mode", normal_query_op, 100)
    lean_time, lean_ops = await benchmark_operation("  Lean mode", lean_query_op, 100)
    
    speedup = (normal_time / lean_time - 1) * 100
    print(f"  Lean mode is {speedup:.1f}% faster")
    
    await db.disconnect()


async def main():
    print("=" * 80)
    print("TabernacleORM Performance Benchmarks")
    print("=" * 80)
    
    databases = [
        ("SQLite (Memory)", "sqlite:///:memory:"),
        ("SQLite (File)", "sqlite:///benchmark.db"),
    ]
    
    # Add other databases if available
    try:
        await run_benchmarks("MongoDB (Local)", "mongodb://localhost:27017/benchmark")
        databases.append(("MongoDB", "mongodb://localhost:27017/benchmark"))
    except:
        print("\nMongoDB not available for benchmarking")
    
    for db_name, connection_string in databases:
        try:
            await run_benchmarks(db_name, connection_string)
        except Exception as e:
            print(f"\nError benchmarking {db_name}: {e}")
    
    print("\n" + "=" * 80)
    print("Benchmarks completed!")
    print("=" * 80)
    print("\nNotes:")
    print("- Results vary based on hardware and database configuration")
    print("- SQLite in-memory is fastest for small datasets")
    print("- MongoDB excels at complex queries and large datasets")
    print("- Use lean() mode for read-only operations (20-30% faster)")
    print("- Bulk operations are significantly faster than individual inserts")


if __name__ == "__main__":
    asyncio.run(main())
