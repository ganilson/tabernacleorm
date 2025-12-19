"""
Loan Controller - Demonstrates populate, where queries, filtering, sorting
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models import Loan, User
from services.loan_service import LoanService
from utils.dependencies import get_current_user, require_role

router = APIRouter()


class LoanCreate(BaseModel):
    book_id: str
    duration_days: Optional[int] = None


class LoanResponse(BaseModel):
    id: str
    book_id: str
    user_id: str
    loan_date: datetime
    due_date: datetime
    return_date: Optional[datetime]
    status: str
    fine_amount: float
    
    class Config:
        from_attributes = True


class LoanReturnRequest(BaseModel):
    book_id: str


@router.get("/", response_model=List[LoanResponse])
async def get_loans_filtered(skip: int = Query(0), limit: int = Query(20)):
    """Get loans with filtering: status in [active, overdue], sorted by due_date - Demonstrates $in filter and sort"""
    loans = await LoanService.get_loans_with_filter(skip=skip, limit=limit)
    return loans


@router.get("/my-loans", response_model=List[LoanResponse])
async def get_my_loans(current_user: User = Depends(get_current_user)):
    """Get current user's loans with populated book data - Demonstrates populate"""
    user_id = str(getattr(current_user, 'id', ''))
    loans = await LoanService.get_user_loans(user_id)
    return loans


@router.get("/overdue", response_model=List[LoanResponse])
async def get_overdue_loans(current_user: User = Depends(require_role("librarian"))):
    """Get all overdue loans using where query - Demonstrates where() clauses (librarian only)"""
    loans = await LoanService.get_overdue_loans()
    return loans


@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(loan_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific loan with populated relationships - Demonstrates populate"""
    loan = await LoanService.get_loan(loan_id)
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    
    # Users can only see their own loans (unless admin)
    user_id = str(getattr(current_user, 'id', ''))
    loan_user = getattr(loan, 'user_id', None)
    loan_user_id = str(getattr(loan_user, 'id', '')) if hasattr(loan_user, 'id') else str(loan_user) if loan_user else None
    
    if loan_user_id != user_id and getattr(current_user, 'role', None) != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    return loan


@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def create_loan(loan: LoanCreate, current_user: User = Depends(get_current_user)):
    """Create a new loan (borrow a book)"""
    try:
        new_loan = await LoanService.create_loan(
            book_id=loan.book_id,
            user_id=str(getattr(current_user, 'id', '')),
            duration_days=loan.duration_days
        )
        return new_loan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{loan_id}/return", response_model=LoanResponse)
async def return_loan(loan_id: str, current_user: User = Depends(get_current_user)):
    """Return a borrowed book using findOneAndUpdate - Demonstrates findOneAndUpdate"""
    try:
        loan = await LoanService.get_loan(loan_id)
        if not loan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
        
        user_id = str(getattr(current_user, 'id', ''))
        loan_user = getattr(loan, 'user_id', None)
        loan_user_id = str(getattr(loan_user, 'id', '')) if hasattr(loan_user, 'id') else str(loan_user) if loan_user else None
        
        if loan_user_id != user_id and getattr(current_user, 'role', None) != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        updated_loan = await LoanService.return_loan(loan_id)
        return updated_loan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
