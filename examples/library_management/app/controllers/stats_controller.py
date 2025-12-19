"""
Statistics Controller
Demonstrates: aggregations, groupBy, lookup
"""

from fastapi import APIRouter, Depends
from services.loan_service import LoanService
from utils.dependencies import require_role
from models import User

router = APIRouter()


@router.get("/loans")
async def get_loan_statistics(current_user: User = Depends(require_role("librarian"))):
    """
    Get overall loan statistics
    Demonstrates: aggregation, groupBy
    """
    stats = await LoanService.get_loan_statistics()
    return stats


@router.get("/dashboard")
async def get_dashboard_stats(current_user: User = Depends(require_role("librarian"))):
    """
    Get dashboard statistics
    Demonstrates: multiple aggregations
    """
    from app.services.book_service import BookService
    from app.models import Book, User as UserModel, Author
    
    # Get various stats
    loan_stats = await LoanService.get_loan_statistics()
    category_stats = await BookService.get_category_statistics()
    most_borrowed = await BookService.get_most_borrowed_books(5)
    
    # Count totals
    total_books = await Book.count()
    total_users = await UserModel.count()
    total_authors = await Author.count()
    
    return {
        "totals": {
            "books": total_books,
            "users": total_users,
            "authors": total_authors
        },
        "loans": loan_stats,
        "categories": category_stats,
        "most_borrowed": most_borrowed
    }
