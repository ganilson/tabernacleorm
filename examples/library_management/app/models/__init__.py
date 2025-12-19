"""
Library Management System - Models
Demonstrates TabernacleORM models with relationships
"""

from datetime import datetime
from tabernacleorm import Model, fields


class User(Model):
    """User model with role-based access"""
    username = fields.StringField(required=True, unique=True)
    email = fields.StringField(required=True, unique=True)
    password_hash = fields.StringField(required=True)
    full_name = fields.StringField(required=True)
    role = fields.StringField(default="member")  # admin, librarian, member
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        collection = "users"


class Author(Model):
    """Author model"""
    name = fields.StringField(required=True)
    bio = fields.StringField()
    birth_year = fields.IntegerField(nullable=True)
    nationality = fields.StringField()
    created_at = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        collection = "authors"


class Category(Model):
    """Book category model"""
    name = fields.StringField(required=True, unique=True)
    description = fields.StringField()
    created_at = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        collection = "categories"


class Book(Model):
    """Book model with relationships"""
    isbn = fields.StringField(required=True, unique=True)
    title = fields.StringField(required=True)
    description = fields.StringField()
    author_id = fields.ForeignKey(Author, required=True)
    category_id = fields.ForeignKey(Category, required=True)
    publisher = fields.StringField()
    publication_year = fields.IntegerField()
    pages = fields.IntegerField()
    copies_available = fields.IntegerField(default=1)
    total_copies = fields.IntegerField(default=1)
    language = fields.StringField(default="Portuguese")
    cover_image = fields.StringField(nullable=True)
    created_at = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        collection = "books"


class Loan(Model):
    """Loan/Borrow model"""
    book_id = fields.ForeignKey(Book, required=True)
    user_id = fields.ForeignKey(User, required=True)
    loan_date = fields.DateTimeField(auto_now_add=True)
    due_date = fields.DateTimeField(required=True)
    return_date = fields.DateTimeField(nullable=True)
    status = fields.StringField(default="active")  # active, returned, overdue
    fine_amount = fields.FloatField(default=0.0)
    notes = fields.StringField(nullable=True)
    
    class Meta:
        collection = "loans"


class Reservation(Model):
    """Book reservation model"""
    book_id = fields.ForeignKey(Book, required=True)
    user_id = fields.ForeignKey(User, required=True)
    reservation_date = fields.DateTimeField(auto_now_add=True)
    expiry_date = fields.DateTimeField(required=True)
    status = fields.StringField(default="pending")  # pending, fulfilled, cancelled, expired
    notified = fields.BooleanField(default=False)
    
    class Meta:
        collection = "reservations"
