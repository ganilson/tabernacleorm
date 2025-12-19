"""
Simple field types for TabernacleORM.
"""

from typing import Any, Optional

from .base import Field


class IntegerField(Field):
    """Integer field type."""
    
    _field_type = "integer"
    
    def __init__(
        self,
        *,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        auto_increment: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.auto_increment = auto_increment
    
    def validate(self, value: Any) -> Optional[int]:
        value = super().validate(value)
        if value is None:
            return None
        
        if not isinstance(value, int):
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise ValueError(f"Field '{self.name}' must be an integer")
        
        if self.min_value is not None and value < self.min_value:
            raise ValueError(
                f"Field '{self.name}' must be >= {self.min_value}"
            )
        
        if self.max_value is not None and value > self.max_value:
            raise ValueError(
                f"Field '{self.name}' must be <= {self.max_value}"
            )
        
        return value
    
    def get_schema(self) -> dict:
        schema = super().get_schema()
        schema["auto_increment"] = self.auto_increment
        return schema


class StringField(Field):
    """String field with optional max length."""
    
    _field_type = "string"
    
    def __init__(
        self,
        *,
        max_length: int = 255,
        min_length: int = 0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.max_length = max_length
        self.min_length = min_length
    
    def validate(self, value: Any) -> Optional[str]:
        value = super().validate(value)
        if value is None:
            return None
        
        if not isinstance(value, str):
            value = str(value)
        
        if len(value) > self.max_length:
            raise ValueError(
                f"Field '{self.name}' exceeds max length of {self.max_length}"
            )
        
        if len(value) < self.min_length:
            raise ValueError(
                f"Field '{self.name}' must be at least {self.min_length} characters"
            )
        
        return value
    
    def get_schema(self) -> dict:
        schema = super().get_schema()
        schema["max_length"] = self.max_length
        return schema


class TextField(Field):
    """Text field for longer strings without length limit."""
    
    _field_type = "text"
    
    def validate(self, value: Any) -> Optional[str]:
        value = super().validate(value)
        if value is None:
            return None
        return str(value)


class FloatField(Field):
    """Float/decimal field type."""
    
    _field_type = "float"
    
    def __init__(
        self,
        *,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any) -> Optional[float]:
        value = super().validate(value)
        if value is None:
            return None
        
        if not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ValueError(f"Field '{self.name}' must be a number")
        
        value = float(value)
        
        if self.min_value is not None and value < self.min_value:
            raise ValueError(
                f"Field '{self.name}' must be >= {self.min_value}"
            )
        
        if self.max_value is not None and value > self.max_value:
            raise ValueError(
                f"Field '{self.name}' must be <= {self.max_value}"
            )
        
        return value


class BooleanField(Field):
    """Boolean field type."""
    
    _field_type = "boolean"
    
    def __init__(self, *, default: bool = False, **kwargs):
        super().__init__(default=default, **kwargs)
    
    def validate(self, value: Any) -> Optional[bool]:
        value = super().validate(value)
        if value is None:
            return None
        return bool(value)
    
    def to_db(self, value: Any) -> Any:
        """Convert to int for SQL databases."""
        if value is None:
            return None
        return 1 if value else 0
    
    def from_db(self, value: Any) -> Optional[bool]:
        """Convert from int to bool."""
        if value is None:
            return None
        return bool(value)
