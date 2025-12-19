"""
Book Controller
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from models import Book, User
from services.book_service import BookService
from utils.dependencies import get_current_user, require_role

router = APIRouter()


class BookCreate(BaseModel):
    title: str
    isbn: str
    author_id: str
    category_id: str
    description: Optional[str] = None
    available_copies: int = 1
    total_copies: int = 1


class BookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    available_copies: Optional[int] = None
    total_copies: Optional[int] = None


class BookResponse(BaseModel):
    id: str
    title: str
    isbn: str
    author_id: str
    category_id: str
    description: Optional[str]
    available_copies: int
    total_copies: int
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[BookResponse])
async def get_books(skip: int = Query(0), limit: int = Query(20)):
    """Get all books with pagination and populated author/category"""
    books = await BookService.get_all_books(skip=skip, limit=limit)
    return books


@router.get("/available", response_model=List[BookResponse])
async def get_available_books(skip: int = Query(0), limit: int = Query(20)):
    """Get only available books using where query"""
    books = await BookService.get_available_books(skip=skip, limit=limit)
    return books


@router.get("/search", response_model=List[BookResponse])
async def search_books(q: str = Query(...), skip: int = Query(0), limit: int = Query(20)):
    """Search books by title or description (regex search)"""
    books = await BookService.search_books(q, skip=skip, limit=limit)
    return books


@router.get("/author/{author_id}", response_model=List[BookResponse])
async def get_books_by_author(author_id: str, skip: int = Query(0), limit: int = Query(20)):
    """Get books by specific author with populated author data"""
    books = await BookService.get_books_by_author(author_id, skip=skip, limit=limit)
    return books


@router.get("/category/{category_id}", response_model=List[BookResponse])
async def get_books_by_category(category_id: str, skip: int = Query(0), limit: int = Query(20)):
    """Get books by specific category with populate"""
    books = await BookService.get_books_by_category(category_id, skip=skip, limit=limit)
    return books


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: str):
    """Get a specific book with populated relationships"""
    book = await BookService.get_book(book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(book: BookCreate, current_user: User = Depends(require_role("librarian"))):
    """Create a new book (librarian only)"""
    try:
        new_book = await BookService.create_book(
            title=book.title,
            isbn=book.isbn,
            author_id=book.author_id,
            category_id=book.category_id,
            description=book.description,
            available_copies=book.available_copies,
            total_copies=book.total_copies
        )
        return new_book
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(book_id: str, book_update: BookUpdate, current_user: User = Depends(require_role("admin"))):
    """Update a book using findOneAndUpdate (admin only)"""
    try:
        updated_book = await BookService.update_book(book_id, book_update.dict(exclude_unset=True))
        if not updated_book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        return updated_book
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: str, current_user: User = Depends(require_role("admin"))):
    """Delete a book using findOneAndDelete (admin only)"""
    success = await BookService.delete_book(book_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return None
