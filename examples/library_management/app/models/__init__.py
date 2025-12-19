"""
Models for Library Management System
"""

from tabernacleorm import Model, Field, BooleanField, StringField, DateTimeField, ForeignKey, FloatField, IntegerField
from datetime import datetime
from typing import Optional


class User(Model):
    """User model"""
    username: str = Field(unique=True, index=True, required=True)
    email: str = Field(unique=True, index=True)
    password_hash: str = StringField(required=True)
    full_name: str = StringField(max_length=100)
    role: str = Field(default="member")  # admin, librarian, member
    is_active: bool = BooleanField(default=True)
    created_at: datetime = DateTimeField(auto_now_add=True)
    updated_at: datetime = DateTimeField(auto_now_add=True)
    
    class Config:
        table_name = "users"


class Author(Model):
    """Author model"""
    name: str = StringField(index=True, required=True)
    email: Optional[str] = StringField(required=False)
    bio: Optional[str] = StringField(max_length=500, required=False)
    created_at: datetime = DateTimeField(auto_now_add=True)
    
    class Config:
        table_name = "authors"


class Category(Model):
    """Category model"""
    name: str = StringField(unique=True, index=True, required=True)
    description: Optional[str] = StringField(required=False)
    created_at: datetime = DateTimeField(auto_now_add=True)
    
    class Config:
        table_name = "categories"


class Book(Model):
    """Book model"""
    title: str = StringField(index=True, required=True)
    isbn: str = StringField(unique=True, index=True, required=True)
    author_id = ForeignKey("Author")
    category_id = ForeignKey("Category")
    description: Optional[str] = StringField(required=False)
    available_copies: int = IntegerField(default=1)
    total_copies: int = IntegerField(default=1)
    published_date: Optional[datetime] = DateTimeField(required=False)
    created_at: datetime = DateTimeField(auto_now_add=True)
    updated_at: datetime = DateTimeField(auto_now_add=True)
    
    class Config:
        table_name = "books"


class Loan(Model):
    """Loan model"""
    book_id = ForeignKey("Book")
    user_id = ForeignKey("User")
    loan_date: datetime = DateTimeField(auto_now_add=True)
    due_date: datetime = DateTimeField(required=True)
    return_date: Optional[datetime] = DateTimeField(required=False)
    status: str = StringField(default="active")  # active, returned, overdue
    fine_amount: float = FloatField(default=0.0)
    created_at: datetime = DateTimeField(auto_now_add=True)
    updated_at: datetime = DateTimeField(auto_now_add=True)
    
    class Config:
        table_name = "loans"


class Reservation(Model):
    """Reservation model"""
    book_id = ForeignKey("Book")
    user_id = ForeignKey("User")
    reservation_date: datetime = DateTimeField(auto_now_add=True)
    status: str = StringField(default="pending")  # pending, ready, cancelled
    created_at: datetime = DateTimeField(auto_now_add=True)
    updated_at: datetime = DateTimeField(auto_now_add=True)
    
    class Config:
        table_name = "reservations"


__all__ = ["User", "Author", "Category", "Book", "Loan", "Reservation"]
