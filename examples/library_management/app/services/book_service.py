"""
Book Service - Business logic for book operations
Demonstrates: populate, complex queries, groupBy
"""

from typing import List, Optional, Dict
from datetime import datetime
from models import Book, Author, Category, Loan


class BookService:
    """Service for book operations"""
    
    @staticmethod
    async def get_all_books(
        category_id: Optional[str] = None,
        author_id: Optional[str] = None,
        available_only: bool = False,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Book]:
        """
        Get all books with filters and populate
        Demonstrates: populate, complex filtering
        """
        query = {}
        
        if category_id:
            query["category_id"] = category_id
        
        if author_id:
            query["author_id"] = author_id
        
        if available_only:
            query["copies_available"] = {"$gt": 0}
        
        # Build query
        qs = Book.find(query).skip(skip).limit(limit).sort("-created_at")
        
        # Populate author and category
        books = await qs.populate("author_id").populate("category_id").exec()
        
        # Filter by search if provided
        if search:
            search_lower = search.lower()
            books = [
                b for b in books
                if search_lower in b.title.lower() or
                   search_lower in (b.description or "").lower()
            ]
        
        return books
    
    @staticmethod
    async def get_book_by_id(book_id: str) -> Optional[Book]:
        """
        Get book by ID with populated relationships
        Demonstrates: populate
        """
        book = await Book.findById(book_id)
        if not book:
            return None
        
        # Populate relationships
        author = await Author.findById(book.author_id)
        category = await Category.findById(book.category_id)
        
        book.author_id = author
        book.category_id = category
        
        return book
    
    @staticmethod
    async def create_book(book_data: dict) -> Book:
        """Create a new book"""
        return await Book.create(**book_data)
    
    @staticmethod
    async def update_book(book_id: str, book_data: dict) -> Optional[Book]:
        """Update book"""
        return await Book.findByIdAndUpdate(
            book_id,
            {"$set": book_data},
            new=True
        )
    
    @staticmethod
    async def delete_book(book_id: str) -> bool:
        """Delete book"""
        deleted = await Book.findByIdAndDelete(book_id)
        return deleted is not None
    
    @staticmethod
    async def get_books_by_category() -> Dict[str, List[dict]]:
        """
        Group books by category
        Demonstrates: groupBy aggregation
        """
        # Get all books with category populated
        books = await Book.find().populate("category_id").exec()
        
        # Group by category
        grouped = {}
        for book in books:
            if hasattr(book.category_id, 'name'):
                category_name = book.category_id.name
                if category_name not in grouped:
                    grouped[category_name] = []
                
                grouped[category_name].append({
                    "id": str(book.id),
                    "title": book.title,
                    "isbn": book.isbn,
                    "copies_available": book.copies_available
                })
        
        return grouped
    
    @staticmethod
    async def get_category_statistics() -> List[dict]:
        """
        Get statistics per category
        Demonstrates: groupBy with aggregation
        """
        books = await Book.find().populate("category_id").exec()
        
        # Group and aggregate
        stats = {}
        for book in books:
            if hasattr(book.category_id, 'name'):
                category_name = book.category_id.name
                
                if category_name not in stats:
                    stats[category_name] = {
                        "category": category_name,
                        "total_books": 0,
                        "total_copies": 0,
                        "available_copies": 0
                    }
                
                stats[category_name]["total_books"] += 1
                stats[category_name]["total_copies"] += book.total_copies
                stats[category_name]["available_copies"] += book.copies_available
        
        return list(stats.values())
    
    @staticmethod
    async def get_most_borrowed_books(limit: int = 10) -> List[dict]:
        """
        Get most borrowed books
        Demonstrates: lookup (join) and aggregation
        """
        # Get all loans
        loans = await Loan.find().populate("book_id").exec()
        
        # Count loans per book
        book_counts = {}
        for loan in loans:
            if hasattr(loan.book_id, 'id'):
                book_id = str(loan.book_id.id)
                
                if book_id not in book_counts:
                    book_counts[book_id] = {
                        "book": loan.book_id,
                        "loan_count": 0
                    }
                
                book_counts[book_id]["loan_count"] += 1
        
        # Sort by count and get top N
        sorted_books = sorted(
            book_counts.values(),
            key=lambda x: x["loan_count"],
            reverse=True
        )[:limit]
        
        # Format result
        result = []
        for item in sorted_books:
            book = item["book"]
            result.append({
                "id": str(book.id),
                "title": book.title,
                "isbn": book.isbn,
                "loan_count": item["loan_count"]
            })
        
        return result
