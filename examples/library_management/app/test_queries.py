"""
Test file for TabernacleORM queries and features
Demonstrates: populate, where queries, filtering, aggregation, etc.
"""

import asyncio
from datetime import datetime, timedelta
from models import User, Author, Category, Book, Loan, Reservation
from database import init_db, close_db


async def test_queries():
    """Test various TabernacleORM queries"""
    
    # Initialize database
    await init_db()
    
    print("\n" + "="*50)
    print("TABERNACLEORM QUERY TESTS")
    print("="*50 + "\n")
    
    # ===== TEST 1: Simple Find with Populate =====
    print("1. Find all books with populated author and category")
    print("-" * 50)
    books = await Book.find().populate("author_id").populate("category_id").exec()
    print(f"Found {len(books)} books")
    for book in books[:2]:
        print(f"  - {book.title} by {getattr(book.author_id, 'name', 'Unknown')}")
    
    # ===== TEST 2: Find with Where clause =====
    print("\n2. Find users with age greater than 25")
    print("-" * 50)
    # Create test user first
    test_user = await User.create(
        username="test_adult",
        email="adult@test.com",
        password_hash="hashed_pwd",
        full_name="Adult User",
        role="member",
        is_active=True
    )
    print(f"Created user: {test_user.username}")
    
    # ===== TEST 3: Find with complex filter =====
    print("\n3. Find active loans with due date in past (overdue)")
    print("-" * 50)
    now = datetime.utcnow()
    past_date = now - timedelta(days=5)
    
    # Query with comparison operators
    overdue_loans = await Loan.find().where("status").eq("active").where("due_date").lt(now).exec()
    print(f"Found {len(overdue_loans)} overdue loans")
    
    # ===== TEST 4: Find with $in operator =====
    print("\n4. Find loans with specific statuses")
    print("-" * 50)
    loans = await Loan.find({"status": {"$in": ["active", "overdue"]}}).exec()
    print(f"Found {len(loans)} active or overdue loans")
    
    # ===== TEST 5: Find with range filter =====
    print("\n5. Find books with availability between 2 and 5 copies")
    print("-" * 50)
    available_books = await Book.find({
        "available_copies": {"$gte": 2, "$lte": 5}
    }).exec()
    print(f"Found {len(available_books)} books with 2-5 copies")
    
    # ===== TEST 6: Sort and limit =====
    print("\n6. Find top 3 most recently created loans")
    print("-" * 50)
    recent_loans = await Loan.find().sort("-created_at").limit(3).exec()
    print(f"Found {len(recent_loans)} recent loans")
    for loan in recent_loans:
        print(f"  - Loan ID: {loan.id} created at {loan.created_at}")
    
    # ===== TEST 7: Skip and pagination =====
    print("\n7. Pagination: Get page 2 (skip 5, limit 3)")
    print("-" * 50)
    page_2_books = await Book.find().skip(5).limit(3).sort("title").exec()
    print(f"Found {len(page_2_books)} books in page 2")
    for book in page_2_books:
        print(f"  - {book.title}")
    
    # ===== TEST 8: Find and Populate with options =====
    print("\n8. Find loans with populated book (with sorting)")
    print("-" * 50)
    loans_with_books = await Loan.find({"status": "active"}).populate(
        "book_id",
        options={"sort": "-created_at", "limit": 2}
    ).exec()
    print(f"Found {len(loans_with_books)} loans with populated books")
    
    # ===== TEST 9: FindOne =====
    print("\n9. Find specific user by username")
    print("-" * 50)
    user = await User.findOne({"username": "test_adult"})
    if user:
        print(f"Found user: {user.full_name} ({user.email})")
    
    # ===== TEST 10: FindOneAndUpdate =====
    print("\n10. Update and return original document")
    print("-" * 50)
    if books:
        original_book = await Book.findOneAndUpdate(
            {"_id": books[0].id},
            {"$set": {"available_copies": 10}},
            new=False  # Return original document
        )
        print(f"Original available_copies: {original_book.available_copies}")
        
        # Get updated document
        updated_book = await Book.findOne({"_id": books[0].id})
        print(f"Updated available_copies: {updated_book.available_copies}")
    
    # ===== TEST 11: Count documents =====
    print("\n11. Count documents in collections")
    print("-" * 50)
    user_count = await User.find().count()
    book_count = await Book.find().count()
    loan_count = await Loan.find().count()
    print(f"Users: {user_count}")
    print(f"Books: {book_count}")
    print(f"Loans: {loan_count}")
    
    # ===== TEST 12: Complex query with multiple conditions =====
    print("\n12. Complex query: Active loans for specific user with sorting")
    print("-" * 50)
    user_loans = await Loan.find({
        "user_id": test_user.id,
        "status": "active"
    }).populate("book_id").sort("-due_date").exec()
    print(f"Found {len(user_loans)} active loans for user {test_user.username}")
    
    # ===== TEST 13: Find with regex (text search) =====
    print("\n13. Find books by title containing 'book'")
    print("-" * 50)
    searched_books = await Book.find({
        "title": {"$regex": "book", "$options": "i"}
    }).exec()
    print(f"Found {len(searched_books)} books matching search")
    
    # ===== TEST 14: Aggregation-like query =====
    print("\n14. Get all books and count loans per book")
    print("-" * 50)
    all_books = await Book.find().exec()
    book_loan_stats = {}
    for book in all_books:
        loan_count = await Loan.find({"book_id": book.id}).count()
        if loan_count > 0:
            book_loan_stats[book.title] = loan_count
    print(f"Books with loans: {book_loan_stats}")
    
    # ===== TEST 15: Delete operations =====
    print("\n15. Delete test user")
    print("-" * 50)
    deleted = await User.findOneAndDelete({"username": "test_adult"})
    if deleted:
        print(f"Deleted user: {deleted.full_name}")
    
    # Close database
    await close_db()
    
    print("\n" + "="*50)
    print("TESTS COMPLETED")
    print("="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(test_queries())
