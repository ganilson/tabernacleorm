"""
Special fields for TabernacleORM.
"""

from typing import Any, List, Optional, Union, Dict
from uuid import UUID, uuid4
import json

from .base import Field


class UUIDField(Field):
    """UUID field."""
    
    _field_type = "uuid"
    
    def __init__(self, *, binary: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.binary = binary
        if self.default == "uuid4":
            self.default = uuid4
    
    def validate(self, value: Any) -> Optional[UUID]:
        value = super().validate(value)
        if value is None:
            return None
        
        if isinstance(value, UUID):
            return value
        
        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError:
                pass
        
        if isinstance(value, bytes):
            try:
                return UUID(bytes=value)
            except ValueError:
                pass
        
        raise ValueError(f"Field '{self.name}' must be a valid UUID")
    
    def to_db(self, value: Any) -> Any:
        """Convert to string or binary for storage."""
        if value is None:
            return None
        if not isinstance(value, UUID):
            value = self.validate(value)
        
        return value  # Engine handles serialization (string vs binary)


class JSONField(Field):
    """JSON field for storing dictionaries/lists."""
    
    _field_type = "json"
    
    def validate(self, value: Any) -> Optional[Union[Dict, List]]:
        value = super().validate(value)
        if value is None:
            return None
        
        if not isinstance(value, (dict, list)):
            raise ValueError(f"Field '{self.name}' must be a dict or list")
        
        try:
            # Verify it's serializable
            json.dumps(value)
        except (TypeError, ValueError):
            raise ValueError(f"Field '{self.name}' must be JSON serializable")
        
        return value
    
    def to_db(self, value: Any) -> Any:
        # Engine handles serialization
        return value
    
    def from_db(self, value: Any) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        return value


class ArrayField(Field):
    """Array field for storing lists of items."""
    
    _field_type = "array"
    
    def __init__(self, item_type: Field = None, **kwargs):
        super().__init__(**kwargs)
        self.item_type = item_type
        # If no default provided, default to empty list if not required
        if self.default is None and not self.required:
            self.default = list
    
    def validate(self, value: Any) -> Optional[List]:
        value = super().validate(value)
        if value is None:
            return None
        
        if not isinstance(value, list):
            raise ValueError(f"Field '{self.name}' must be a list")
        
        if self.item_type:
            # Validate each item
            validated_list = []
            for i, item in enumerate(value):
                try:
                    # Create temporary field instance if needed or use item_type
                    # We need to set the name for error messages
                    self.item_type.name = f"{self.name}[{i}]"
                    validated_list.append(self.item_type.validate(item))
                except ValueError as e:
                    raise ValueError(f"Invalid item in array '{self.name}': {str(e)}")
            return validated_list
        
        return value
