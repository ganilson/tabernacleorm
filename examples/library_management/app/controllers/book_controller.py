"""
Book Controller
Demonstrates: CRUD operations, populate, groupBy
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel
from app.services.book_service import BookService
from app.utils.dependencies import get_current_user, require_role
from app.models import User

router = APIRouter()


class BookCreate(BaseModel):
    isbn: str
    title: str
    description: Optional[str] = None
    author_id: str
    category_id: str
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    pages: Optional[int] = None
    total_copies: int = 1
    language: str = "Portuguese"


class BookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    publisher: Optional[str] = None
    total_copies: Optional[int] = None
    copies_available: Optional[int] = None


@router.get("/")
async def list_books(
    category_id: Optional[str] = None,
    author_id: Optional[str] = None,
    available_only: bool = False,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """
    List all books with filters
    Demonstrates: populate, complex filtering
    """
    books = await BookService.get_all_books(
        category_id=category_id,
        author_id=author_id,
        available_only=available_only,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return [
        {
            "id": str(b.id),
            "isbn": b.isbn,
            "title": b.title,
            "description": b.description,
            "author": b.author_id.name if hasattr(b.author_id, 'name') else None,
            "category": b.category_id.name if hasattr(b.category_id, 'name') else None,
            "copies_available": b.copies_available,
            "total_copies": b.total_copies
        }
        for b in books
    ]


@router.get("/{book_id}")
async def get_book(book_id: str):
    """
    Get book by ID with populated relationships
    Demonstrates: populate
    """
    book = await BookService.get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {
        "id": str(book.id),
        "isbn": book.isbn,
        "title": book.title,
        "description": book.description,
        "author": {
            "id": str(book.author_id.id),
            "name": book.author_id.name,
            "bio": book.author_id.bio
        } if hasattr(book.author_id, 'id') else None,
        "category": {
            "id": str(book.category_id.id),
            "name": book.category_id.name
        } if hasattr(book.category_id, 'id') else None,
        "publisher": book.publisher,
        "publication_year": book.publication_year,
        "pages": book.pages,
        "copies_available": book.copies_available,
        "total_copies": book.total_copies,
        "language": book.language
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_book(
    book: BookCreate,
    current_user: User = Depends(require_role("librarian"))
):
    """Create a new book (librarian+)"""
    new_book = await BookService.create_book(book.dict())
    return {"id": str(new_book.id), "title": new_book.title}


@router.put("/{book_id}")
async def update_book(
    book_id: str,
    book: BookUpdate,
    current_user: User = Depends(require_role("librarian"))
):
    """Update book (librarian+)"""
    updated_book = await BookService.update_book(book_id, book.dict(exclude_unset=True))
    if not updated_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {"id": str(updated_book.id), "title": updated_book.title}


@router.delete("/{book_id}")
async def delete_book(
    book_id: str,
    current_user: User = Depends(require_role("admin"))
):
    """Delete book (admin only)"""
    deleted = await BookService.delete_book(book_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {"message": "Book deleted successfully"}


@router.get("/grouped/by-category")
async def get_books_by_category():
    """
    Get books grouped by category
    Demonstrates: groupBy
    """
    grouped = await BookService.get_books_by_category()
    return grouped


@router.get("/stats/by-category")
async def get_category_stats():
    """
    Get statistics per category
    Demonstrates: groupBy with aggregation
    """
    stats = await BookService.get_category_statistics()
    return stats


@router.get("/stats/most-borrowed")
async def get_most_borrowed(limit: int = Query(10, ge=1, le=50)):
    """
    Get most borrowed books
    Demonstrates: lookup (join) and aggregation
    """
    books = await BookService.get_most_borrowed_books(limit)
    return books
