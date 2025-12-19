"""
FastAPI Decorators for Read Replica Control
"""

from functools import wraps
from typing import Callable
import contextvars

# Context variable to store read preference for current request
_read_preference_context = contextvars.ContextVar('read_preference', default=None)


def get_read_preference():
    """Get the current read preference from context"""
    return _read_preference_context.get()


def set_read_preference(preference: str):
    """Set the read preference for current context"""
    _read_preference_context.set(preference)


def clear_read_preference():
    """Clear the read preference"""
    _read_preference_context.set(None)


def read_from_primary(func: Callable) -> Callable:
    """
    Decorator to force endpoint to read from PRIMARY replica
    
    Use for:
    - Critical data that must be up-to-date
    - Data just written (read-after-write consistency)
    - User account information
    - Transaction-related queries
    
    Example:
        @app.get("/users/me")
        @read_from_primary
        async def get_current_user(current_user: User = Depends(get_current_user)):
            # This will read from PRIMARY
            user = await User.findById(current_user.id).exec()
            return user
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        set_read_preference('primary')
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            clear_read_preference()
    
    return wrapper


def read_from_secondary(func: Callable) -> Callable:
    """
    Decorator to force endpoint to read from SECONDARY replicas
    
    Use for:
    - Search and list operations
    - Analytics and reports
    - Non-critical data
    - High-volume read endpoints
    
    Example:
        @app.get("/products/search")
        @read_from_secondary
        async def search_products(query: str):
            # This will read from SECONDARY
            products = await Product.find({"name": {"$regex": query}}).exec()
            return products
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        set_read_preference('secondary')
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            clear_read_preference()
    
    return wrapper


def read_from_secondary_preferred(func: Callable) -> Callable:
    """
    Decorator to prefer SECONDARY replicas, fallback to PRIMARY
    
    Use for:
    - Most read operations (good default)
    - Balance between consistency and performance
    - When eventual consistency is acceptable
    
    Example:
        @app.get("/books")
        @read_from_secondary_preferred
        async def list_books():
            # This will prefer SECONDARY, fallback to PRIMARY
            books = await Book.find().exec()
            return books
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        set_read_preference('secondaryPreferred')
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            clear_read_preference()
    
    return wrapper


def read_from_nearest(func: Callable) -> Callable:
    """
    Decorator to read from nearest replica (lowest latency)
    
    Use for:
    - Geographically distributed applications
    - When latency is most important
    - Global applications with users worldwide
    
    Example:
        @app.get("/content")
        @read_from_nearest
        async def get_content():
            # This will read from nearest node
            content = await Content.find().exec()
            return content
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        set_read_preference('nearest')
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            clear_read_preference()
    
    return wrapper


# Alias for convenience
read_primary = read_from_primary
read_secondary = read_from_secondary
read_secondary_preferred = read_from_secondary_preferred
read_nearest = read_from_nearest
