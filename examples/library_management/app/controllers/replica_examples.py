"""
Example: Read Replica Control in Library Management System
Demonstrates both methods of controlling read replicas
"""

from fastapi import APIRouter, Depends
from typing import List
from models import Book, User, Loan
from utils.dependencies import get_current_user

# Import decorators
from tabernacleorm.decorators import (
    read_from_primary,
    read_from_secondary,
    read_from_secondary_preferred,
    read_from_nearest
)

router = APIRouter()


# ============================================================================
# METHOD 1: Query-level control with .read_from()
# ============================================================================

@router.get("/books/search")
async def search_books_query_level(query: str):
    """
    Search books using query-level read preference
    Uses .read_from() method on the query
    """
    # Force read from SECONDARY (good for searches)
    books = await Book.find(
        {"title": {"$regex": query, "$options": "i"}}
    ).read_from("secondary").exec()
    
    return [{"id": str(b.id), "title": b.title} for b in books]


@router.get("/users/me/query")
async def get_current_user_query_level(current_user: User = Depends(get_current_user)):
    """
    Get current user using query-level read preference
    Uses .read_from() method on the query
    """
    # Force read from PRIMARY (critical user data)
    user = await User.findById(current_user.id).read_from("primary").exec()
    
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email
    }


@router.get("/books/analytics/query")
async def get_book_analytics_query_level():
    """
    Get book analytics using query-level read preference
    """
    # Read from SECONDARY (analytics don't need real-time data)
    total_books = await Book.count().read_from("secondary")
    
    books = await Book.find().read_from("secondary").exec()
    
    by_category = {}
    for book in books:
        category = book.category_id
        by_category[category] = by_category.get(category, 0) + 1
    
    return {
        "total_books": total_books,
        "by_category": by_category
    }


# ============================================================================
# METHOD 2: Endpoint-level control with decorators
# ============================================================================

@router.get("/books/search-decorated")
@read_from_secondary  # Decorator: force SECONDARY
async def search_books_decorated(query: str):
    """
    Search books using endpoint-level decorator
    All queries in this endpoint read from SECONDARY
    """
    books = await Book.find(
        {"title": {"$regex": query, "$options": "i"}}
    ).exec()  # No need for .read_from() - decorator handles it
    
    return [{"id": str(b.id), "title": b.title} for b in books]


@router.get("/users/me/decorated")
@read_from_primary  # Decorator: force PRIMARY
async def get_current_user_decorated(current_user: User = Depends(get_current_user)):
    """
    Get current user using endpoint-level decorator
    All queries in this endpoint read from PRIMARY
    """
    user = await User.findById(current_user.id).exec()
    
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email
    }


@router.get("/books/list-decorated")
@read_from_secondary_preferred  # Decorator: prefer SECONDARY, fallback to PRIMARY
async def list_books_decorated(skip: int = 0, limit: int = 20):
    """
    List books using endpoint-level decorator
    Prefers SECONDARY but falls back to PRIMARY if needed
    """
    books = await Book.find().skip(skip).limit(limit).exec()
    
    return [
        {
            "id": str(b.id),
            "title": b.title,
            "author": b.author_id
        }
        for b in books
    ]


@router.get("/stats/dashboard-decorated")
@read_from_secondary  # Decorator: all stats from SECONDARY
async def get_dashboard_stats_decorated():
    """
    Get dashboard statistics using endpoint-level decorator
    All analytics queries read from SECONDARY
    """
    total_books = await Book.count()
    total_users = await User.count()
    active_loans = await Loan.find({"status": "active"}).count()
    
    return {
        "total_books": total_books,
        "total_users": total_users,
        "active_loans": active_loans
    }


# ============================================================================
# MIXED: Combining both methods
# ============================================================================

@router.get("/books/mixed")
@read_from_secondary_preferred  # Default for endpoint: prefer SECONDARY
async def get_books_mixed(book_id: str = None):
    """
    Mixed approach: decorator sets default, but specific queries can override
    """
    if book_id:
        # Override decorator: force PRIMARY for specific book lookup
        book = await Book.findById(book_id).read_from("primary").exec()
        return {"book": book}
    else:
        # Use decorator's preference (secondaryPreferred)
        books = await Book.find().limit(20).exec()
        return {"books": books}


# ============================================================================
# COMPARISON: When to use each method
# ============================================================================

"""
METHOD 1: .read_from() - Query-level control
✅ Use when:
- Different queries in same endpoint need different preferences
- Fine-grained control needed
- Mixing critical and non-critical queries

Example:
    @router.get("/dashboard")
    async def dashboard():
        # Critical: read from primary
        user = await User.findById(user_id).read_from("primary").exec()
        
        # Non-critical: read from secondary
        stats = await Stats.find().read_from("secondary").exec()
        
        return {"user": user, "stats": stats}


METHOD 2: Decorators - Endpoint-level control
✅ Use when:
- All queries in endpoint have same requirements
- Cleaner, more declarative code
- Endpoint purpose is clear (search, analytics, user data, etc.)

Example:
    @router.get("/search")
    @read_from_secondary  # All searches from secondary
    async def search(query: str):
        products = await Product.find({"name": query}).exec()
        categories = await Category.find().exec()
        return {"products": products, "categories": categories}


BEST PRACTICES:

1. User Data (just created/updated) → PRIMARY
   @read_from_primary or .read_from("primary")

2. Searches, Lists → SECONDARY
   @read_from_secondary or .read_from("secondary")

3. Analytics, Reports → SECONDARY
   @read_from_secondary or .read_from("secondary")

4. General reads → SECONDARY_PREFERRED (good default)
   @read_from_secondary_preferred or .read_from("secondaryPreferred")

5. Global apps → NEAREST
   @read_from_nearest or .read_from("nearest")
"""
