"""
Statistics Service
"""

from typing import Dict
from models import Book, User, Loan, Reservation


class StatsService:
    """Service for statistics operations"""
    
    @staticmethod
    async def get_system_stats() -> Dict:
        """Get system-wide statistics"""
        # Count documents
        total_books = await Book.find().count()
        total_users = await User.find().count()
        
        # Count active loans
        active_loans = await Loan.find({"status": "active"}).count()
        
        # Count overdue loans
        from datetime import datetime
        overdue_loans = await Loan.find({
            "status": "active",
            "due_date": {"$lt": datetime.now()}
        }).count()
        
        # Count reserved books
        reserved_books = await Reservation.find({"status": "pending"}).count()
        
        # Calculate total fines
        returned_loans = await Loan.find({"status": "returned"}).exec()
        total_revenue = sum(loan.fine_amount for loan in returned_loans)
        
        return {
            "total_books": total_books,
            "total_users": total_users,
            "active_loans": active_loans,
            "overdue_loans": overdue_loans,
            "reserved_books": reserved_books,
            "total_revenue_from_fines": total_revenue
        }
    
    @staticmethod
    async def get_user_stats(user_id: str) -> Dict:
        """Get user-specific statistics"""
        # Count user's loans
        total_loans = await Loan.find({"user_id": user_id}).count()
        active_loans = await Loan.find({"user_id": user_id, "status": "active"}).count()
        
        # Count overdue loans
        from datetime import datetime
        overdue_loans = await Loan.find({
            "user_id": user_id,
            "status": "active",
            "due_date": {"$lt": datetime.now()}
        }).count()
        
        # Calculate total fines
        returned_loans = await Loan.find({
            "user_id": user_id,
            "status": "returned"
        }).exec()
        total_fines = sum(loan.fine_amount for loan in returned_loans)
        
        return {
            "total_loans": total_loans,
            "active_loans": active_loans,
            "overdue_loans": overdue_loans,
            "total_fines": total_fines
        }
