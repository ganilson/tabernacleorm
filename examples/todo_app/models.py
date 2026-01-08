"""
Models for TODO App
Demonstrates relationships, foreign keys, and all TabernacleORM features
"""
from typing import List, Optional, Union
from datetime import datetime
from tabernacleorm import Model
from tabernacleorm.fields import StringField, IntegerField, BooleanField, DateTimeField, ForeignKey, OneToMany

class User(Model):
    """User model - has many TodoLists"""
    name: str = StringField(max_length=100)
    email: str = StringField(max_length=255, unique=True)
    created_at: datetime = DateTimeField(auto_now_add=True, default=None)
    
    # OneToMany relationship: User has many TodoLists
    todo_lists: Optional[List["TodoList"]] = OneToMany("TodoList", back_populates="user_id")
    
    class Config:
        table_name = "users"

class TodoList(Model):
    """TodoList model - belongs to User, has many TodoItems"""
    title: str = StringField(max_length=200)
    description: Optional[str] = StringField(max_length=1000, default="")
    created_at: datetime = DateTimeField(auto_now_add=True, default=None)
    updated_at: datetime = DateTimeField(auto_now=True, default=None)
    
    # Foreign Key: Each list belongs to a user
    # Union[int, str] makes it work with both SQL (int) and MongoDB (str ObjectId)
    user_id: Optional[Union[int, str]] = ForeignKey("User")
    
    # OneToMany relationship: TodoList has many TodoItems
    items: Optional[List["TodoItem"]] = OneToMany("TodoItem", back_populates="list_id")
    
    class Config:
        table_name = "todo_lists"

class TodoItem(Model):
    """TodoItem model - belongs to TodoList"""
    title: str = StringField(max_length=300)
    description: Optional[str] = StringField(max_length=2000, default="")
    completed: bool = BooleanField(default=False)
    priority: int = IntegerField(default=0)  # 0=low, 1=medium, 2=high
    due_date: Optional[datetime] = DateTimeField(default=None)
    created_at: datetime = DateTimeField(auto_now_add=True, default=None)
    completed_at: Optional[datetime] = DateTimeField(default=None)
    
    # Foreign Key: Each item belongs to a list
    list_id: Optional[Union[int, str]] = ForeignKey("TodoList")
    
    class Config:
        table_name = "todo_items"
