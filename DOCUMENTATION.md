# TabernacleORM - Complete Documentation Index

This file serves as an index to all documentation available for TabernacleORM.

## 📚 Core Documentation

### Main README
- **[README.md](README.md)** - Main project documentation (displayed on PyPI)
  - Overview and features
  - Installation and quick start
  - Database connections
  - MongoDB replica sets
  - Read replica control
  - Complete examples

### Feature Guides
- **[FEATURES.md](FEATURES.md)** - Complete feature documentation
  - 25+ Mongoose-inspired features
  - Populate (nested, field selection, filters)
  - Query operators (gt, lt, in_, or_, and_)
  - Find and modify methods
  - Advanced queries (exists, distinct, lean)
  - Migration guide from v2.0 to v2.1

### MongoDB & Replicas
- **[MONGODB_REPLICAS.md](MONGODB_REPLICAS.md)** - MongoDB replica sets guide
  - What are replica sets
  - High availability and failover
  - Read scalability (3x performance)
  - Read preferences explained
  - Write concerns explained
  - Setup instructions
  - Production deployment

- **[REPLICA_QUICKSTART.md](REPLICA_QUICKSTART.md)** - Quick start for read replicas
  - Decorator usage
  - When to use each preference
  - Performance comparison
  - Configuration examples

- **[READ_REPLICA_CONTROL.md](READ_REPLICA_CONTROL.md)** - Complete replica control guide
  - Query-level control
  - Endpoint-level decorators
  - Decision guide
  - Best practices
  - Performance impact

## 🎯 Examples

### Featured: Library Management System
- **[examples/library_management/README.md](examples/library_management/README.md)**
  - Production-ready FastAPI application
  - JWT authentication with role-based access
  - 6 models with relationships
  - Clean MVC architecture
  - 20+ API endpoints
  - Populate, GroupBy, Lookup demonstrations

- **[examples/library_management/MONGODB_REPLICAS.md](examples/library_management/MONGODB_REPLICAS.md)**
  - MongoDB replica configuration for library system
  - Read preferences per endpoint
  - Write concerns for different operations
  - Setup guide

### FastAPI Examples (10 APIs)
- **[examples/FASTAPI_EXAMPLES.md](examples/FASTAPI_EXAMPLES.md)** - Guide to all FastAPI examples
  1. E-commerce API - Products, orders, reviews, analytics
  2. Blog API - Posts, nested comments, follow system
  3. Real Estate API - Geospatial queries, location search
  4. Task Management - Projects, assignments, statistics
  5. Social Media - Posts, followers, feed
  6. Analytics - Event tracking, aggregations
  7. Multi-tenant SaaS - API key auth, tenant isolation
  8. Messaging - Conversations, messages
  9. Inventory - Warehouses, stock management
  10. Booking System - Resources, time slots

### Core Feature Examples
- **[examples/test_populate.py](examples/test_populate.py)** - Populate demonstrations
- **[examples/test_query_operators.py](examples/test_query_operators.py)** - Query operators
- **[examples/test_find_and_modify.py](examples/test_find_and_modify.py)** - Find and modify
- **[examples/test_advanced_queries.py](examples/test_advanced_queries.py)** - Advanced queries
- **[examples/test_sorting_pagination.py](examples/test_sorting_pagination.py)** - Sorting & pagination
- **[examples/test_hooks_validation.py](examples/test_hooks_validation.py)** - Hooks & validation

### Database Examples
- **[examples/connection_examples.py](examples/connection_examples.py)** - All connection methods
- **[examples/database_mongodb.py](examples/database_mongodb.py)** - MongoDB-specific features
- **[examples/performance_benchmarks.py](examples/performance_benchmarks.py)** - Performance tests
- **[examples/test_replicas.py](examples/test_replicas.py)** - Replica sets demo

## 🚀 Quick Navigation

### Getting Started
1. Read [README.md](README.md) - Overview and installation
2. Try [Library Management Example](examples/library_management/README.md) - Complete working app
3. Explore [FEATURES.md](FEATURES.md) - All available features

### For Production
1. [MONGODB_REPLICAS.md](MONGODB_REPLICAS.md) - Setup replica sets
2. [REPLICA_QUICKSTART.md](REPLICA_QUICKSTART.md) - Control read replicas
3. [Production Deployment](README.md#production-deployment) - Best practices

### For Learning
1. [FastAPI Examples](examples/FASTAPI_EXAMPLES.md) - 10 complete APIs
2. [Core Examples](examples/) - Feature-specific examples
3. [Library Management](examples/library_management/README.md) - Full application

## 📖 Documentation by Topic

### Authentication & Security
- [Library Management - JWT Auth](examples/library_management/README.md#authentication)
- [Library Management - Role-Based Access](examples/library_management/README.md#api-endpoints)

### Database Connections
- [README - Database Connections](README.md#database-connections)
- [Connection Examples](examples/connection_examples.py)

### Replica Sets & High Availability
- [MongoDB Replicas Guide](MONGODB_REPLICAS.md)
- [Read Replica Control](REPLICA_QUICKSTART.md)
- [Library Management - MongoDB Config](examples/library_management/MONGODB_REPLICAS.md)

### Advanced Queries
- [FEATURES - Populate](FEATURES.md#populate-join-eager-loading)
- [FEATURES - Query Operators](FEATURES.md#query-operators)
- [Library Management - GroupBy & Lookup](examples/library_management/README.md#tabernacleorm-features-demonstrated)

### Performance
- [Performance Benchmarks](examples/performance_benchmarks.py)
- [Replica Performance](MONGODB_REPLICAS.md#performance-comparison)
- [Read Replica Impact](REPLICA_QUICKSTART.md#performance-impact)

## 🔗 External Links

- **PyPI**: https://pypi.org/project/tabernacleorm/
- **GitHub**: https://github.com/ganilson/tabernacleorm
- **Issues**: https://github.com/ganilson/tabernacleorm/issues

---

**All documentation is available in the repository and will be displayed on PyPI via README.md**
