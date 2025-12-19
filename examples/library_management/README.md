# Library Management System - Complete Guide

## 📚 Overview

A **production-ready** Library Management System built with **FastAPI** and **TabernacleORM**, demonstrating best practices in API development, authentication, and database operations.

### Features

✅ **JWT Authentication** - Secure token-based authentication  
✅ **Role-Based Access Control** - Admin, Librarian, Member roles  
✅ **Complete CRUD Operations** - Books, Authors, Categories, Loans  
✅ **Advanced Queries** - Populate, GroupBy, Lookup demonstrations  
✅ **Business Logic** - Loan management, fine calculation, stock tracking  
✅ **Clean Architecture** - Separated Models, Services, Controllers  
✅ **Comprehensive API** - 20+ endpoints with full documentation  

---

## 🏗️ Project Structure

```
library_management/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── database.py             # Database setup
│   ├── models/                 # TabernacleORM models
│   │   └── __init__.py         # User, Book, Author, Category, Loan, Reservation
│   ├── services/               # Business logic
│   │   ├── auth_service.py     # Authentication
│   │   ├── book_service.py     # Book operations (populate, groupBy, lookup)
│   │   └── loan_service.py     # Loan operations
│   ├── controllers/            # API routes
│   │   ├── auth_controller.py  # /api/auth/*
│   │   ├── book_controller.py  # /api/books/*
│   │   ├── loan_controller.py  # /api/loans/*
│   │   └── stats_controller.py # /api/stats/*
│   └── utils/                  # Utilities
│       ├── security.py         # JWT, password hashing
│       └── dependencies.py     # FastAPI dependencies
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Navigate to project directory
cd examples/library_management

# Install dependencies
pip install -r requirements.txt

# Or install TabernacleORM from PyPI
pip install tabernacleorm fastapi uvicorn python-jose passlib
```

### 2. Configuration

Create `.env` file:

```env
DATABASE_URL=sqlite:///library.db
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Run the Application

```bash
# Development mode
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Access API Documentation

Open your browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🔐 Authentication

### Register a New User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepassword",
    "full_name": "John Doe",
    "role": "member"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "1",
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "member"
  }
}
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "securepassword"
  }'
```

### Using the Token

```bash
# Add to Authorization header
curl -X GET http://localhost:8000/api/books \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 📖 API Endpoints

### Authentication (`/api/auth`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/register` | Register new user | No |
| POST | `/login` | Login user | No |

### Books (`/api/books`)

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/` | List all books | No | - |
| GET | `/{book_id}` | Get book details | No | - |
| POST | `/` | Create book | Yes | Librarian+ |
| PUT | `/{book_id}` | Update book | Yes | Librarian+ |
| DELETE | `/{book_id}` | Delete book | Yes | Admin |
| GET | `/grouped/by-category` | Books grouped by category | No | - |
| GET | `/stats/by-category` | Category statistics | No | - |
| GET | `/stats/most-borrowed` | Most borrowed books | No | - |

### Loans (`/api/loans`)

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| POST | `/` | Borrow a book | Yes | Member+ |
| POST | `/{loan_id}/return` | Return a book | Yes | Member+ |
| GET | `/my-loans` | Get my loans | Yes | Member+ |
| GET | `/overdue` | Get overdue loans | Yes | Librarian+ |
| GET | `/history` | Get borrowing history | Yes | Member+ |

### Statistics (`/api/stats`)

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/loans` | Loan statistics | Yes | Librarian+ |
| GET | `/dashboard` | Dashboard stats | Yes | Librarian+ |

---

## 💡 TabernacleORM Features Demonstrated

### 1. Populate (Join/Eager Loading)

**Simple Populate:**
```python
# Get books with author and category populated
books = await Book.find().populate("author_id").populate("category_id").exec()

for book in books:
    print(f"{book.title} by {book.author_id.name}")
```

**Populate with Field Selection:**
```python
# Only load specific fields
books = await Book.find().populate("author_id", select=["name", "bio"]).exec()
```

**Example in BookService:**
```python
async def get_all_books(self, ...):
    books = await Book.find(query)\
        .populate("author_id")\
        .populate("category_id")\
        .exec()
    return books
```

### 2. GroupBy (Aggregation)

**Group Books by Category:**
```python
# Get all books with category populated
books = await Book.find().populate("category_id").exec()

# Group by category
grouped = {}
for book in books:
    category_name = book.category_id.name
    if category_name not in grouped:
        grouped[category_name] = []
    grouped[category_name].append(book)
```

**Example in BookService:**
```python
async def get_category_statistics(self):
    books = await Book.find().populate("category_id").exec()
    
    stats = {}
    for book in books:
        category = book.category_id.name
        if category not in stats:
            stats[category] = {
                "total_books": 0,
                "total_copies": 0,
                "available_copies": 0
            }
        
        stats[category]["total_books"] += 1
        stats[category]["total_copies"] += book.total_copies
        stats[category]["available_copies"] += book.copies_available
    
    return list(stats.values())
```

### 3. Lookup (Join with Aggregation)

**Most Borrowed Books:**
```python
# Get all loans with book populated
loans = await Loan.find().populate("book_id").exec()

# Count loans per book
book_counts = {}
for loan in loans:
    book_id = str(loan.book_id.id)
    if book_id not in book_counts:
        book_counts[book_id] = {
            "book": loan.book_id,
            "loan_count": 0
        }
    book_counts[book_id]["loan_count"] += 1

# Sort by count
sorted_books = sorted(
    book_counts.values(),
    key=lambda x: x["loan_count"],
    reverse=True
)
```

### 4. Complex Queries

**Multiple Filters with Chaining:**
```python
# Available books in specific category
books = await Book.find()\
    .where("category_id", category_id)\
    .where("copies_available").gt(0)\
    .sort("-publication_year")\
    .limit(20)\
    .exec()
```

**Date-based Filtering:**
```python
# Overdue loans
from datetime import datetime

loans = await Loan.find({"status": "active"}).exec()
overdue = [loan for loan in loans if loan.due_date < datetime.now()]
```

---

## 🎯 Usage Examples

### Example 1: Borrow a Book

```python
import requests

# 1. Login
login_response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"username": "john_doe", "password": "securepassword"}
)
token = login_response.json()["access_token"]

# 2. Get available books
books_response = requests.get(
    "http://localhost:8000/api/books?available_only=true",
    headers={"Authorization": f"Bearer {token}"}
)
books = books_response.json()
book_id = books[0]["id"]

# 3. Borrow the book
loan_response = requests.post(
    "http://localhost:8000/api/loans",
    headers={"Authorization": f"Bearer {token}"},
    json={"book_id": book_id}
)
print(loan_response.json())
```

### Example 2: Get Statistics

```python
# Get category statistics
stats_response = requests.get(
    "http://localhost:8000/api/books/stats/by-category"
)
stats = stats_response.json()

for category in stats:
    print(f"{category['category']}: {category['total_books']} books")
```

### Example 3: Search Books

```python
# Search books by title
books = requests.get(
    "http://localhost:8000/api/books?search=python&limit=10"
).json()

for book in books:
    print(f"{book['title']} by {book['author']}")
```

---

## 🔧 Configuration Options

### Database

```python
# SQLite (default)
DATABASE_URL=sqlite:///library.db

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost/library

# MySQL
DATABASE_URL=mysql://user:password@localhost/library

# MongoDB (single instance)
DATABASE_URL=mongodb://localhost:27017/library

# MongoDB Replica Set (recommended for production)
DATABASE_URL=mongodb://host1:27017,host2:27017,host3:27017/library?replicaSet=rs0
MONGODB_READ_PREFERENCE=secondaryPreferred
MONGODB_WRITE_CONCERN=majority
```

### MongoDB Replica Sets

The library system supports **MongoDB replica sets** for high availability and read scalability:

**Benefits:**
- ✅ **Automatic Failover**: If primary fails, a secondary is elected
- ✅ **Read Scalability**: Distribute reads across 3+ nodes (3x performance)
- ✅ **Data Redundancy**: Multiple copies prevent data loss
- ✅ **Zero Downtime**: Maintenance without stopping the app

**Configuration:**

```env
# Local Replica Set
DATABASE_URL=mongodb://localhost:27017,localhost:27018,localhost:27019/library?replicaSet=rs0

# MongoDB Atlas (Cloud)
DATABASE_URL=mongodb+srv://user:pass@cluster.mongodb.net/library?retryWrites=true&w=majority

# Read Preference
MONGODB_READ_PREFERENCE=secondaryPreferred  # Read from secondaries when possible

# Write Concern
MONGODB_WRITE_CONCERN=majority  # Wait for majority acknowledgment
```

**Read Preferences:**
- `primary` - All reads from primary (strongest consistency)
- `secondary` - All reads from secondaries (max scalability)
- `secondaryPreferred` - Prefer secondaries, fallback to primary (recommended)
- `primaryPreferred` - Prefer primary, fallback to secondaries
- `nearest` - Read from nearest node (lowest latency)

**Write Concerns:**
- `0` - No acknowledgment (fastest, no guarantee)
- `1` - Acknowledged by primary (default, good balance)
- `majority` - Acknowledged by majority (strongest durability)

👉 **[Complete MongoDB Replica Guide](MONGODB_REPLICAS.md)**

### JWT Settings

```python
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Loan Settings

```python
DEFAULT_LOAN_DAYS=14
MAX_LOANS_PER_USER=5
FINE_PER_DAY=0.50
```

---

## 🧪 Testing

### Manual Testing with curl

```bash
# Register admin user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@lib.com","password":"admin123","full_name":"Admin User","role":"admin"}'

# Create a book (requires librarian+ role)
curl -X POST http://localhost:8000/api/books \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "isbn": "978-0-123456-78-9",
    "title": "Python Programming",
    "author_id": "1",
    "category_id": "1",
    "total_copies": 5
  }'

# Borrow a book
curl -X POST http://localhost:8000/api/loans \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"book_id": "1"}'

# Return a book
curl -X POST http://localhost:8000/api/loans/1/return \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📊 Database Schema

### Models

**User**
- username (unique)
- email (unique)
- password_hash
- full_name
- role (admin/librarian/member)
- is_active

**Author**
- name
- bio
- birth_year
- nationality

**Category**
- name (unique)
- description

**Book**
- isbn (unique)
- title
- description
- author_id (ForeignKey → Author)
- category_id (ForeignKey → Category)
- publisher
- publication_year
- pages
- copies_available
- total_copies
- language

**Loan**
- book_id (ForeignKey → Book)
- user_id (ForeignKey → User)
- loan_date
- due_date
- return_date
- status (active/returned/overdue)
- fine_amount

**Reservation**
- book_id (ForeignKey → Book)
- user_id (ForeignKey → User)
- reservation_date
- expiry_date
- status (pending/fulfilled/cancelled/expired)

---

## 🎓 Learning Resources

### TabernacleORM Documentation
- [Main README](../../../README.md)
- [Features Guide](../../../FEATURES.md)
- [FastAPI Examples](../../FASTAPI_EXAMPLES.md)

### Key Concepts Demonstrated

1. **MVC Architecture**: Models, Services (business logic), Controllers (routes)
2. **JWT Authentication**: Token generation, verification, role-based access
3. **Database Relationships**: ForeignKey, populate (eager loading)
4. **Advanced Queries**: GroupBy, Lookup, complex filtering
5. **Business Logic**: Stock management, fine calculation, validation

---

## 🚀 Production Deployment

### Environment Variables

```bash
# Production settings
DATABASE_URL=postgresql://user:pass@prod-db:5432/library
SECRET_KEY=super-secret-production-key
DEBUG=False
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Running with Docker

```bash
docker build -t library-api .
docker run -p 8000:8000 -e DATABASE_URL=sqlite:///library.db library-api
```

---

## 📝 License

This is an example project for demonstrating TabernacleORM capabilities.

---

## 🤝 Contributing

This example is part of the TabernacleORM project. For contributions, please refer to the main repository.

---

## 📞 Support

- **Documentation**: [TabernacleORM Docs](../../../README.md)
- **Issues**: [GitHub Issues](https://github.com/ganilson/tabernacleorm/issues)
- **Examples**: [More Examples](../../)

---

**Built with ❤️ using TabernacleORM and FastAPI**
