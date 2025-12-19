"""
Date and time fields for TabernacleORM.
"""

from typing import Any, Optional, Union
from datetime import datetime, date

from .base import Field


class DateTimeField(Field):
    """DateTime field."""
    
    _field_type = "datetime"
    
    def __init__(
        self,
        *,
        auto_now: bool = False,
        auto_now_add: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
        
        if auto_now or auto_now_add:
            self.default = datetime.now
    
    def validate(self, value: Any) -> Optional[datetime]:
        value = super().validate(value)
        if value is None:
            return None
        
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass
        
        raise ValueError(f"Field '{self.name}' must be a datetime object")
    
    def to_db(self, value: Any) -> Any:
        """Convert to ISO format string for storage."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return value
    
    def from_db(self, value: Any) -> Optional[datetime]:
        """Convert from ISO string to datetime."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass
        return value


class DateField(Field):
    """Date field."""
    
    _field_type = "date"
    
    def __init__(
        self,
        *,
        auto_now: bool = False,
        auto_now_add: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
        
        if auto_now or auto_now_add:
            self.default = date.today
    
    def validate(self, value: Any) -> Optional[date]:
        value = super().validate(value)
        if value is None:
            return None
        
        if isinstance(value, datetime):
            return value.date()
        
        if isinstance(value, date):
            return value
        
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                pass
        
        raise ValueError(f"Field '{self.name}' must be a date object")
    
    def to_db(self, value: Any) -> Any:
        """Convert to ISO format string for storage."""
        if value is None:
            return None
        if isinstance(value, date):
            return value.isoformat()
        return value
    
    def from_db(self, value: Any) -> Optional[date]:
        """Convert from ISO string to date."""
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                pass
        return value
