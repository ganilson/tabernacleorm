# TabernacleORM 🏛️

A lightweight, intuitive, and Pythonic ORM for database operations.

## ✨ Features

- **Simple Model Definition** - Define models using Python classes with typed fields
- **Intuitive Query API** - Chain methods like `filter()`, `order_by()`, `limit()`
- **Auto Migrations** - Built-in migration system for schema versioning
- **SQLite Support** - Works out of the box with SQLite (more databases coming soon)
- **Type Hints** - Full type annotation support for better IDE experience

## 📦 Installation

```bash
pip install tabernacleorm
```

Or install from source:

```bash
pip install -e .
```

## 🚀 Quick Start

### 1. Define Your Models

```python
from tabernacleorm import Model, Database, StringField, IntegerField, DateTimeField

# Initialize database
db = Database("my_app.db", echo=True)

# Define your model
class User(Model):
    name = StringField(max_length=100, nullable=False)
    email = StringField(max_length=255, unique=True)
    age = IntegerField(nullable=True)
    created_at = DateTimeField(auto_now_add=True)

# Connect model to database
User.set_database(db)

# Create the table
db.create_table(User)
```

### 2. Create Records

```python
# Method 1: Create and save
user = User(name="John Doe", email="john@example.com", age=30)
user.save()

# Method 2: Create directly
user = User.create(name="Jane Doe", email="jane@example.com", age=25)
```

### 3. Query Records

```python
# Get all users
users = User.all()

# Filter users
young_users = User.filter(age__lt=30)
john = User.get(name="John Doe")

# Chain queries
users = User.filter(age__gte=18).order_by("-created_at").limit(10)

# Advanced filtering
admins = User.filter(email__contains="@admin.com")
recent = User.filter(created_at__gte=yesterday)
```

### 4. Update Records

```python
user = User.get(id=1)
user.name = "John Smith"
user.save()

# Or bulk update
User.filter(age__lt=18).update(status="minor")
```

### 5. Delete Records

```python
user = User.get(id=1)
user.delete()

# Or bulk delete
User.filter(active=False).delete()
```

## 📋 Field Types

| Field Type | SQL Type | Python Type |
|------------|----------|-------------|
| `IntegerField` | INTEGER | `int` |
| `StringField` | VARCHAR | `str` |
| `TextField` | TEXT | `str` |
| `FloatField` | REAL | `float` |
| `BooleanField` | BOOLEAN | `bool` |
| `DateTimeField` | DATETIME | `datetime` |
| `DateField` | DATE | `date` |
| `ForeignKey` | INTEGER | `int` |

## 🔍 Query Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `__gt` | Greater than | `age__gt=18` |
| `__gte` | Greater or equal | `age__gte=18` |
| `__lt` | Less than | `age__lt=65` |
| `__lte` | Less or equal | `age__lte=65` |
| `__ne` | Not equal | `status__ne="inactive"` |
| `__in` | In list | `id__in=[1, 2, 3]` |
| `__contains` | Contains substring | `name__contains="John"` |
| `__startswith` | Starts with | `email__startswith="admin"` |
| `__endswith` | Ends with | `email__endswith=".com"` |
| `__isnull` | Is null check | `deleted_at__isnull=True` |

## 🔄 Migrations

```python
from tabernacleorm import Database
from tabernacleorm.migrations import Migration, MigrationManager, Schema

db = Database("my_app.db")
manager = MigrationManager(db)

class AddStatusColumn(Migration):
    version = "001"
    description = "Add status column to users table"
    
    def up(self, db):
        db.execute(Schema.add_column("users", "status", "VARCHAR(50) DEFAULT 'active'"))
    
    def down(self, db):
        # SQLite doesn't support DROP COLUMN easily
        pass

manager.register(AddStatusColumn())
manager.migrate()
```

## 🛠️ Development

```bash
# Clone the repository
git clone https://github.com/yourusername/tabernacleorm.git
cd tabernacleorm

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src tests
isort src tests
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
