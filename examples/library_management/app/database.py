"""
Database connection and initialization
"""

from tabernacleorm import connect
from app.config import settings

# Database instance
db = None


async def init_db():
    """Initialize database connection"""
    global db
    db = connect(settings.DATABASE_URL)
    await db.connect()
    
    # Import models to ensure they're registered
    from app.models import User, Author, Category, Book, Loan, Reservation
    
    # Create tables
    await User.createTable()
    await Author.createTable()
    await Category.createTable()
    await Book.createTable()
    await Loan.createTable()
    await Reservation.createTable()
    
    print(f"✅ Database connected: {settings.DATABASE_URL}")
    print("✅ Tables created successfully")


async def close_db():
    """Close database connection"""
    global db
    if db:
        await db.disconnect()
        print("✅ Database disconnected")


async def get_db():
    """Dependency for getting database"""
    return db
