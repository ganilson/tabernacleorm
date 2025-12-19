"""
Base field class for TabernacleORM.
"""

from typing import Any, Callable, List, Optional, Type


class Field:
    """
    Base field class for all field types.
    
    Attributes:
        required: Whether the field is required (not nullable)
        default: Default value or callable
        unique: Whether field must be unique
        index: Whether to create an index
        validators: List of validator functions
        primary_key: Whether this is the primary key
    """
    
    _field_type = "base"
    
    def __init__(
        self,
        *,
        required: bool = False,
        default: Any = None,
        unique: bool = False,
        index: bool = False,
        validators: Optional[List[Callable]] = None,
        primary_key: bool = False,
        nullable: bool = True,
        **kwargs
    ):
        self.required = required or not nullable
        self.default = default
        self.unique = unique
        self.index = index
        self.validators = validators or []
        self.primary_key = primary_key
        self.nullable = nullable and not required
        
        # Set by metaclass
        self.name: Optional[str] = None
        self.model: Optional[Type] = None
        
        # Store extra kwargs for subclasses
        self._extra = kwargs
    
    def __set_name__(self, owner: Type, name: str) -> None:
        """Called when field is assigned to a class attribute."""
        self.name = name
        self.model = owner
    
    def __get__(self, obj: Any, objtype: Optional[Type] = None) -> Any:
        """Get field value from instance."""
        if obj is None:
            return self
        return obj.__dict__.get(self.name, self.get_default())
    
    def __set__(self, obj: Any, value: Any) -> None:
        """Set field value on instance."""
        validated = self.validate(value)
        obj.__dict__[self.name] = validated
        
        # Track modification
        if hasattr(obj, "_modified_fields"):
            obj._modified_fields.add(self.name)
    
    def get_default(self) -> Any:
        """Get default value (call if callable)."""
        if callable(self.default) and self.default is not None:
            return self.default()
        return self.default
    
    def validate(self, value: Any) -> Any:
        """
        Validate and convert the value.
        
        Raises:
            ValueError: If validation fails
        """
        # Handle None
        if value is None:
            if self.required:
                raise ValueError(f"Field '{self.name}' is required")
            return None
        
        # Run custom validators
        for validator in self.validators:
            if not validator(value):
                raise ValueError(
                    f"Field '{self.name}' failed validation"
                )
        
        return value
    
    def to_db(self, value: Any) -> Any:
        """Convert Python value to database format."""
        return value
    
    def from_db(self, value: Any) -> Any:
        """Convert database value to Python format."""
        return value
    
    def get_schema(self) -> dict:
        """Get schema definition for this field."""
        return {
            "type": self._field_type,
            "required": self.required,
            "unique": self.unique,
            "index": self.index,
            "primary_key": self.primary_key,
            "default": self.default if not callable(self.default) else None,
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name})>"
