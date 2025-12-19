"""
Loan Service - Business logic for loan operations
Demonstrates: complex queries, populate, date calculations
"""

from datetime import datetime, timedelta
from typing import List, Optional
from app.models import Loan, Book, User
from app.config import settings


class LoanService:
    """Service for loan operations"""
    
    @staticmethod
    async def create_loan(user_id: str, book_id: str) -> Loan:
        """
        Create a new loan
        Demonstrates: business logic, stock management
        """
        # Check if book is available
        book = await Book.findById(book_id)
        if not book:
            raise ValueError("Book not found")
        
        if book.copies_available <= 0:
            raise ValueError("Book not available")
        
        # Check user's active loans
        active_loans = await Loan.find({"user_id": user_id, "status": "active"}).exec()
        if len(active_loans) >= settings.MAX_LOANS_PER_USER:
            raise ValueError(f"Maximum loans ({settings.MAX_LOANS_PER_USER}) reached")
        
        # Create loan
        loan_date = datetime.now()
        due_date = loan_date + timedelta(days=settings.DEFAULT_LOAN_DAYS)
        
        loan = await Loan.create(
            book_id=book_id,
            user_id=user_id,
            loan_date=loan_date,
            due_date=due_date,
            status="active"
        )
        
        # Update book availability
        book.copies_available -= 1
        await book.save()
        
        return loan
    
    @staticmethod
    async def return_loan(loan_id: str) -> Loan:
        """Return a loan"""
        loan = await Loan.findById(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        if loan.status != "active":
            raise ValueError("Loan is not active")
        
        # Calculate fine if overdue
        return_date = datetime.now()
        fine_amount = 0.0
        
        if return_date > loan.due_date:
            days_overdue = (return_date - loan.due_date).days
            fine_amount = days_overdue * settings.FINE_PER_DAY
        
        # Update loan
        loan.return_date = return_date
        loan.status = "returned"
        loan.fine_amount = fine_amount
        await loan.save()
        
        # Update book availability
        book = await Book.findById(loan.book_id)
        if book:
            book.copies_available += 1
            await book.save()
        
        return loan
    
    @staticmethod
    async def get_user_loans(user_id: str, status: Optional[str] = None) -> List[Loan]:
        """
        Get user's loans with populated book info
        Demonstrates: populate
        """
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        
        loans = await Loan.find(query).sort("-loan_date").populate("book_id").exec()
        return loans
    
    @staticmethod
    async def get_overdue_loans() -> List[Loan]:
        """
        Get all overdue loans
        Demonstrates: date filtering, populate
        """
        now = datetime.now()
        
        # Get active loans
        loans = await Loan.find({"status": "active"}).populate("user_id").populate("book_id").exec()
        
        # Filter overdue
        overdue = [loan for loan in loans if loan.due_date < now]
        
        # Update status
        for loan in overdue:
            loan.status = "overdue"
            await loan.save()
        
        return overdue
    
    @staticmethod
    async def get_loan_statistics() -> dict:
        """
        Get loan statistics
        Demonstrates: aggregation, groupBy
        """
        all_loans = await Loan.findMany()
        
        stats = {
            "total_loans": len(all_loans),
            "active_loans": 0,
            "returned_loans": 0,
            "overdue_loans": 0,
            "total_fines": 0.0,
            "by_status": {}
        }
        
        for loan in all_loans:
            # Count by status
            stats["by_status"][loan.status] = stats["by_status"].get(loan.status, 0) + 1
            
            # Count specific statuses
            if loan.status == "active":
                stats["active_loans"] += 1
            elif loan.status == "returned":
                stats["returned_loans"] += 1
            elif loan.status == "overdue":
                stats["overdue_loans"] += 1
            
            # Sum fines
            stats["total_fines"] += loan.fine_amount
        
        return stats
    
    @staticmethod
    async def get_user_borrowing_history(user_id: str) -> dict:
        """
        Get user's complete borrowing history
        Demonstrates: lookup, aggregation
        """
        loans = await Loan.find({"user_id": user_id}).populate("book_id").exec()
        
        history = {
            "total_loans": len(loans),
            "active_loans": 0,
            "returned_loans": 0,
            "total_fines": 0.0,
            "books_borrowed": []
        }
        
        book_set = set()
        
        for loan in loans:
            if loan.status == "active":
                history["active_loans"] += 1
            elif loan.status == "returned":
                history["returned_loans"] += 1
            
            history["total_fines"] += loan.fine_amount
            
            if hasattr(loan.book_id, 'id'):
                book_id = str(loan.book_id.id)
                if book_id not in book_set:
                    book_set.add(book_id)
                    history["books_borrowed"].append({
                        "title": loan.book_id.title,
                        "isbn": loan.book_id.isbn
                    })
        
        return history
