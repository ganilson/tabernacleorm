"""
Book Service - Business logic for book operations
Demonstrates: populate, complex queries, filtering
"""

from typing import List, Optional, Dict
from datetime import datetime
from models import Book, Author, Category, Loan


class BookService:
    """Service for book operations"""
    
    @staticmethod
    async def get_all_books(skip: int = 0, limit: int = 20) -> List[Book]:
        """Get all books with author and category populated"""
        books = await Book.find().populate("author_id").populate("category_id").skip(skip).limit(limit).sort("-created_at").exec()
        return books
    
    @staticmethod
    async def get_book(book_id: str) -> Optional[Book]:
        """Get book by ID with populated relationships"""
        book = await Book.findOne({"_id": book_id}).populate("author_id").populate("category_id").exec()
        return book
    
    @staticmethod
    async def get_available_books(skip: int = 0, limit: int = 20) -> List[Book]:
        """Get only available books"""
        books = await Book.find().where("available_copies").gt(0).populate("author_id").populate("category_id").skip(skip).limit(limit).exec()
        return books
    
    @staticmethod
    async def create_book(
        title: str,
        isbn: str,
        author_id: str,
        category_id: Optional[str] = None,
        description: Optional[str] = None,
        available_copies: int = 1,
        total_copies: int = 1
    ) -> Book:
        """Create a new book"""
        # Check if ISBN already exists
        existing = await Book.findOne({"isbn": isbn})
        if existing:
            raise ValueError("ISBN already exists")
        
        book = await Book.create(
            title=title,
            isbn=isbn,
            author_id=author_id,
            category_id=category_id,
            description=description,
            available_copies=available_copies,
            total_copies=total_copies
        )
        return book
    
    @staticmethod
    async def update_book(book_id: str, book_data: dict) -> Optional[Book]:
        """Update book"""
        book_data["updated_at"] = datetime.utcnow()
        updated = await Book.findOneAndUpdate(
            {"_id": book_id},
            {"$set": book_data},
            new=True
        )
        return updated
    
    @staticmethod
    async def delete_book(book_id: str) -> bool:
        """Delete book"""
        deleted = await Book.findOneAndDelete({"_id": book_id})
        return deleted is not None
    
    @staticmethod
    async def get_books_by_category(category_id: str, skip: int = 0, limit: int = 20) -> List[Book]:
        """Get books by category"""
        books = await Book.find({"category_id": category_id}).populate("author_id").skip(skip).limit(limit).exec()
        return books
    
    @staticmethod
    async def get_books_by_author(author_id: str, skip: int = 0, limit: int = 20) -> List[Book]:
        """Get books by author"""
        books = await Book.find({"author_id": author_id}).populate("category_id").skip(skip).limit(limit).exec()
        return books
    
    @staticmethod
    async def search_books(search_term: str, skip: int = 0, limit: int = 20) -> List[Book]:
        """Search books by title or description"""
        books = await Book.find({
            "$or": [
                {"title": {"$regex": search_term, "$options": "i"}},
                {"description": {"$regex": search_term, "$options": "i"}}
            ]
        }).populate("author_id").populate("category_id").skip(skip).limit(limit).exec()
        return books
    
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
