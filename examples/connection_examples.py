"""
Connection Examples for All Databases
Demonstrates different connection methods and configurations
"""

import asyncio
from tabernacleorm import connect


async def example_sqlite():
    """SQLite - File-based database"""
    print("\n" + "=" * 60)
    print("SQLite Connection Examples")
    print("=" * 60)
    
    # Method 1: File database
    db = connect("sqlite:///myapp.db")
    await db.connect()
    print("Connected to SQLite file database")
    await db.disconnect()
    
    # Method 2: In-memory database (for testing)
    db = connect("sqlite:///:memory:")
    await db.connect()
    print("Connected to SQLite in-memory database")
    await db.disconnect()
    
    # Method 3: With configuration
    db = connect("sqlite:///myapp.db", echo=True, check_same_thread=False)
    await db.connect()
    print("Connected with custom configuration")
    await db.disconnect()


async def example_mongodb():
    """MongoDB - Document database"""
    print("\n" + "=" * 60)
    print("MongoDB Connection Examples")
    print("=" * 60)
    
    # Method 1: Local MongoDB
    try:
        db = connect("mongodb://localhost:27017/myapp")
        await db.connect()
        print("Connected to local MongoDB")
        await db.disconnect()
    except Exception as e:
        print(f"MongoDB not available: {e}")
    
    # Method 2: MongoDB with authentication
    connection_string = "mongodb://username:password@localhost:27017/myapp?authSource=admin"
    print(f"Connection string: {connection_string}")
    
    # Method 3: MongoDB Atlas (cloud)
    atlas_string = "mongodb+srv://username:password@cluster.mongodb.net/myapp?retryWrites=true&w=majority"
    print(f"Atlas connection: {atlas_string}")
    
    # Method 4: MongoDB Replica Set
    replica_string = "mongodb://host1:27017,host2:27017,host3:27017/myapp?replicaSet=rs0"
    print(f"Replica set: {replica_string}")
    
    # Method 5: With options
    options_string = "mongodb://localhost:27017/myapp?maxPoolSize=50&minPoolSize=10&maxIdleTimeMS=30000"
    print(f"With pool options: {options_string}")


async def example_postgresql():
    """PostgreSQL - Relational database"""
    print("\n" + "=" * 60)
    print("PostgreSQL Connection Examples")
    print("=" * 60)
    
    # Method 1: Basic connection
    connection_string = "postgresql://user:password@localhost:5432/myapp"
    print(f"Basic: {connection_string}")
    
    # Method 2: With SSL
    ssl_string = "postgresql://user:password@localhost:5432/myapp?sslmode=require"
    print(f"With SSL: {ssl_string}")
    
    # Method 3: Connection pool settings
    pool_string = "postgresql://user:password@localhost:5432/myapp?min_size=10&max_size=20"
    print(f"With pool: {pool_string}")
    
    # Method 4: Cloud providers
    # Heroku
    heroku_string = "postgresql://user:password@ec2-host.compute-1.amazonaws.com:5432/database"
    print(f"Heroku: {heroku_string}")
    
    # AWS RDS
    rds_string = "postgresql://user:password@mydb.123456.us-east-1.rds.amazonaws.com:5432/myapp"
    print(f"AWS RDS: {rds_string}")
    
    # Google Cloud SQL
    gcp_string = "postgresql://user:password@/myapp?host=/cloudsql/project:region:instance"
    print(f"Google Cloud SQL: {gcp_string}")


async def example_mysql():
    """MySQL - Relational database"""
    print("\n" + "=" * 60)
    print("MySQL Connection Examples")
    print("=" * 60)
    
    # Method 1: Basic connection
    connection_string = "mysql://user:password@localhost:3306/myapp"
    print(f"Basic: {connection_string}")
    
    # Method 2: With charset
    charset_string = "mysql://user:password@localhost:3306/myapp?charset=utf8mb4"
    print(f"With charset: {charset_string}")
    
    # Method 3: Connection pool
    pool_string = "mysql://user:password@localhost:3306/myapp?pool_size=10&pool_recycle=3600"
    print(f"With pool: {pool_string}")
    
    # Method 4: Cloud providers
    # AWS RDS
    rds_string = "mysql://user:password@mydb.123456.us-east-1.rds.amazonaws.com:3306/myapp"
    print(f"AWS RDS: {rds_string}")
    
    # Google Cloud SQL
    gcp_string = "mysql://user:password@/myapp?unix_socket=/cloudsql/project:region:instance"
    print(f"Google Cloud SQL: {gcp_string}")


async def example_environment_variables():
    """Using environment variables for connection strings"""
    print("\n" + "=" * 60)
    print("Environment Variables Examples")
    print("=" * 60)
    
    import os
    
    # Set environment variable (in production, use .env file or system env)
    os.environ["DATABASE_URL"] = "sqlite:///myapp.db"
    
    # Method 1: Direct from environment
    db_url = os.getenv("DATABASE_URL")
    db = connect(db_url)
    await db.connect()
    print(f"Connected using DATABASE_URL: {db_url}")
    await db.disconnect()
    
    # Method 2: With fallback
    db_url = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    print(f"Using with fallback: {db_url}")
    
    # Method 3: Different URLs for different environments
    env = os.getenv("ENVIRONMENT", "development")
    
    db_urls = {
        "development": "sqlite:///dev.db",
        "testing": "sqlite:///:memory:",
        "staging": "postgresql://user:pass@staging-db:5432/myapp",
        "production": "postgresql://user:pass@prod-db:5432/myapp"
    }
    
    db_url = db_urls.get(env)
    print(f"Environment: {env}, URL: {db_url}")


async def example_connection_testing():
    """Test database connections"""
    print("\n" + "=" * 60)
    print("Connection Testing")
    print("=" * 60)
    
    databases = [
        ("SQLite", "sqlite:///test.db"),
        ("MongoDB", "mongodb://localhost:27017/test"),
        ("PostgreSQL", "postgresql://user:pass@localhost:5432/test"),
        ("MySQL", "mysql://user:pass@localhost:3306/test")
    ]
    
    for name, url in databases:
        try:
            db = connect(url)
            await db.connect()
            print(f"✓ {name}: Connected successfully")
            await db.disconnect()
        except Exception as e:
            print(f"✗ {name}: {str(e)[:50]}...")


async def example_multiple_databases():
    """Using multiple databases in one application"""
    print("\n" + "=" * 60)
    print("Multiple Databases Example")
    print("=" * 60)
    
    # Primary database (user data)
    primary_db = connect("sqlite:///users.db")
    await primary_db.connect()
    print("Primary database (users): Connected")
    
    # Analytics database (logs, metrics)
    analytics_db = connect("sqlite:///analytics.db")
    await analytics_db.connect()
    print("Analytics database: Connected")
    
    # Cache database (sessions, temporary data)
    cache_db = connect("sqlite:///cache.db")
    await cache_db.connect()
    print("Cache database: Connected")
    
    # Clean up
    await primary_db.disconnect()
    await analytics_db.disconnect()
    await cache_db.disconnect()


async def example_connection_pooling():
    """Connection pooling configuration"""
    print("\n" + "=" * 60)
    print("Connection Pooling Examples")
    print("=" * 60)
    
    # PostgreSQL with pool settings
    pg_pool = """
    postgresql://user:pass@localhost/myapp?
        min_size=10          # Minimum connections in pool
        &max_size=20         # Maximum connections in pool
        &max_queries=50000   # Max queries per connection
        &max_inactive_connection_lifetime=300  # Seconds
    """
    print(f"PostgreSQL pool config: {pg_pool.strip()}")
    
    # MySQL with pool settings
    mysql_pool = """
    mysql://user:pass@localhost/myapp?
        pool_size=10         # Pool size
        &pool_recycle=3600   # Recycle connections after 1 hour
        &pool_pre_ping=True  # Test connections before using
    """
    print(f"MySQL pool config: {mysql_pool.strip()}")
    
    # MongoDB with pool settings
    mongo_pool = """
    mongodb://localhost/myapp?
        maxPoolSize=50       # Maximum connections
        &minPoolSize=10      # Minimum connections
        &maxIdleTimeMS=30000 # Max idle time (30 seconds)
        &waitQueueTimeoutMS=5000  # Wait timeout (5 seconds)
    """
    print(f"MongoDB pool config: {mongo_pool.strip()}")


async def main():
    """Run all connection examples"""
    print("=" * 60)
    print("TabernacleORM - Database Connection Examples")
    print("=" * 60)
    
    await example_sqlite()
    await example_mongodb()
    await example_postgresql()
    await example_mysql()
    await example_environment_variables()
    await example_connection_testing()
    await example_multiple_databases()
    await example_connection_pooling()
    
    print("\n" + "=" * 60)
    print("All connection examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
