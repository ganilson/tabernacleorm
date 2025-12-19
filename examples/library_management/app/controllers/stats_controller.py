"""
Statistics Controller - Demonstrates count, aggregation, and complex queries
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from models import User
from services.stats_service import StatsService
from utils.dependencies import require_role

router = APIRouter()


class StatsResponse(BaseModel):
    total_books: int
    total_users: int
    active_loans: int
    overdue_loans: int
    reserved_books: int
    total_revenue_from_fines: float


class UserStatsResponse(BaseModel):
    total_loans: int
    active_loans: int
    overdue_loans: int
    total_fines: float


@router.get("/", response_model=StatsResponse)
async def get_stats(current_user: User = Depends(require_role("admin"))):
    """Get system statistics - Demonstrates count() and aggregation queries (admin only)"""
    stats = await StatsService.get_system_stats()
    return stats


@router.get("/my-stats", response_model=UserStatsResponse)
async def get_my_stats(current_user: User = Depends(lambda: None)):
    """Get user's statistics - Demonstrates filtered find() and count() queries"""
    user_id = str(getattr(current_user, 'id', ''))
    stats = await StatsService.get_user_stats(user_id)
    return stats
