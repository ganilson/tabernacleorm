"""
Loan Controller
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.services.loan_service import LoanService
from app.utils.dependencies import get_current_user, require_role
from app.models import User

router = APIRouter()


class LoanCreate(BaseModel):
    book_id: str


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_loan(
    loan_data: LoanCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new loan"""
    try:
        loan = await LoanService.create_loan(str(current_user.id), loan_data.book_id)
        return {
            "id": str(loan.id),
            "book_id": str(loan.book_id),
            "due_date": str(loan.due_date),
            "status": loan.status
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{loan_id}/return")
async def return_loan(
    loan_id: str,
    current_user: User = Depends(get_current_user)
):
    """Return a loan"""
    try:
        loan = await LoanService.return_loan(loan_id)
        return {
            "id": str(loan.id),
            "status": loan.status,
            "fine_amount": loan.fine_amount,
            "return_date": str(loan.return_date)
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/my-loans")
async def get_my_loans(
    status: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get current user's loans"""
    loans = await LoanService.get_user_loans(str(current_user.id), status)
    
    return [
        {
            "id": str(loan.id),
            "book": {
                "title": loan.book_id.title if hasattr(loan.book_id, 'title') else None,
                "isbn": loan.book_id.isbn if hasattr(loan.book_id, 'isbn') else None
            },
            "loan_date": str(loan.loan_date),
            "due_date": str(loan.due_date),
            "return_date": str(loan.return_date) if loan.return_date else None,
            "status": loan.status,
            "fine_amount": loan.fine_amount
        }
        for loan in loans
    ]


@router.get("/overdue")
async def get_overdue_loans(current_user: User = Depends(require_role("librarian"))):
    """Get all overdue loans (librarian+)"""
    loans = await LoanService.get_overdue_loans()
    
    return [
        {
            "id": str(loan.id),
            "user": loan.user_id.username if hasattr(loan.user_id, 'username') else None,
            "book": loan.book_id.title if hasattr(loan.book_id, 'title') else None,
            "due_date": str(loan.due_date),
            "days_overdue": (loan.return_date or loan.due_date).days
        }
        for loan in loans
    ]


@router.get("/history")
async def get_borrowing_history(current_user: User = Depends(get_current_user)):
    """Get user's complete borrowing history"""
    history = await LoanService.get_user_borrowing_history(str(current_user.id))
    return history
