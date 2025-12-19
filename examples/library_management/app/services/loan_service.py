"""
Loan Service - Business logic for loan operations
Demonstrates: populate, where queries, date calculations
"""

from datetime import datetime, timedelta
from typing import List, Optional
from models import Loan, Book, User
from config import settings


class LoanService:
    """Service for loan operations"""
    
    @staticmethod
    async def create_loan(book_id: str, user_id: str, duration_days: Optional[int] = None) -> Loan:
        """Create a new loan"""
        # Check if book exists
        book = await Book.findOne({"_id": book_id})
        if not book:
            raise ValueError("Book not found")
        
        if book.available_copies <= 0:
            raise ValueError("Book not available")
        
        # Check user's active loans using where query
        active_loans = await Loan.find({"user_id": user_id, "status": "active"}).exec()
        if len(active_loans) >= settings.MAX_LOANS_PER_USER:
            raise ValueError(f"Maximum loans ({settings.MAX_LOANS_PER_USER}) reached")
        
        # Create loan
        loan_date = datetime.utcnow()
        duration = duration_days or settings.DEFAULT_LOAN_DAYS
        due_date = loan_date + timedelta(days=duration)
        
        loan = await Loan.create(
            book_id=book_id,
            user_id=user_id,
            due_date=due_date,
            status="active"
        )
        
        # Update book availability
        await Book.findOneAndUpdate(
            {"_id": book_id},
            {"$set": {"available_copies": book.available_copies - 1}}
        )
        
        return loan
    
    @staticmethod
    async def return_loan(loan_id: str) -> Loan:
        """Return a loan"""
        loan = await Loan.findOne({"_id": loan_id})
        if not loan:
            raise ValueError("Loan not found")
        
        if loan.status != "active":
            raise ValueError("Loan is not active")
        
        # Calculate fine if overdue
        return_date = datetime.utcnow()
        fine_amount = 0.0
        
        if return_date > loan.due_date:
            days_overdue = (return_date - loan.due_date).days
            fine_amount = days_overdue * settings.FINE_PER_DAY
        
        # Update loan
        updated_loan = await Loan.findOneAndUpdate(
            {"_id": loan_id},
            {"$set": {
                "return_date": return_date,
                "status": "returned",
                "fine_amount": fine_amount
            }},
            new=True
        )
        
        # Update book availability
        book = await Book.findOne({"_id": loan.book_id})
        if book:
            await Book.findOneAndUpdate(
                {"_id": loan.book_id},
                {"$set": {"available_copies": book.available_copies + 1}}
            )
        
        return updated_loan
    
    @staticmethod
    async def get_loan(loan_id: str) -> Optional[Loan]:
        """Get a specific loan with populated data"""
        loan = await Loan.findOne({"_id": loan_id}).populate("book_id").populate("user_id").exec()
        return loan
    
    @staticmethod
    async def get_user_loans(user_id: str, status: Optional[str] = None) -> List[Loan]:
        """Get user's loans with populated book info"""
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        
        loans = await Loan.find(query).populate("book_id").sort("-loan_date").exec()
        return loans
    
    @staticmethod
    async def get_overdue_loans() -> List[Loan]:
        """Get all overdue loans using where query"""
        now = datetime.utcnow()
        
        # Get active loans with due_date in past
        overdue_loans = await Loan.find().where("status").eq("active").where("due_date").lt(now).populate("book_id").populate("user_id").exec()
        
        # Update status
        for loan in overdue_loans:
            await Loan.findOneAndUpdate(
                {"_id": loan.id},
                {"$set": {"status": "overdue"}}
            )
        
        return overdue_loans
    
    @staticmethod
    async def get_loans_with_filter(skip: int = 0, limit: int = 20) -> List[Loan]:
        """Get loans with complex filtering: active or overdue with sorting"""
        loans = await Loan.find({
            "status": {"$in": ["active", "overdue"]}
        }).populate("book_id").populate("user_id").sort("-due_date").skip(skip).limit(limit).exec()
        return loans
