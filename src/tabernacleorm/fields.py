"""
Field definitions for TabernacleORM models.
"""

from typing import Any, Optional, Type
from datetime import datetime, date


class Field:
    """Base field class for all field types."""
    
    def __init__(
        self,
        primary_key: bool = False,
        nullable: bool = True,
        default: Any = None,
        unique: bool = False,
        index: bool = False,
    ):
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.unique = unique
        self.index = index
        self.name: Optional[str] = None
        self.model: Optional[Type] = None
    
    def __set_name__(self, owner: Type, name: str) -> None:
        self.name = name
        self.model = owner
    
    def __get__(self, obj: Any, objtype: Optional[Type] = None) -> Any:
        if obj is None:
            return self
        return obj.__dict__.get(self.name, self.default)
    
    def __set__(self, obj: Any, value: Any) -> None:
        obj.__dict__[self.name] = self.validate(value)
    
    def validate(self, value: Any) -> Any:
        """Validate and convert the value. Override in subclasses."""
        if value is None and not self.nullable:
            raise ValueError(f"Field '{self.name}' cannot be null")
        return value
    
    def get_sql_type(self) -> str:
        """Return the SQL type for this field. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement get_sql_type()")
    
    def get_column_definition(self) -> str:
        """Generate the SQL column definition."""
        parts = [self.name, self.get_sql_type()]
        
        if self.primary_key:
            parts.append("PRIMARY KEY")
        if not self.nullable:
            parts.append("NOT NULL")
        if self.unique and not self.primary_key:
            parts.append("UNIQUE")
        if self.default is not None:
            parts.append(f"DEFAULT {self._format_default()}")
        
        return " ".join(parts)
    
    def _format_default(self) -> str:
        """Format the default value for SQL."""
        if isinstance(self.default, str):
            return f"'{self.default}'"
        elif isinstance(self.default, bool):
            return "1" if self.default else "0"
        return str(self.default)


class IntegerField(Field):
    """Integer field type."""
    
    def __init__(self, auto_increment: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.auto_increment = auto_increment
    
    def validate(self, value: Any) -> Optional[int]:
        value = super().validate(value)
        if value is None:
            return None
        if not isinstance(value, int):
            try:
                return int(value)
            except (ValueError, TypeError):
                raise ValueError(f"Field '{self.name}' must be an integer")
        return value
    
    def get_sql_type(self) -> str:
        if self.auto_increment:
            return "INTEGER AUTOINCREMENT" if self.primary_key else "INTEGER"
        return "INTEGER"
    
    def get_column_definition(self) -> str:
        if self.primary_key and self.auto_increment:
            return f"{self.name} INTEGER PRIMARY KEY AUTOINCREMENT"
        return super().get_column_definition()


class StringField(Field):
    """String field type with max length."""
    
    def __init__(self, max_length: int = 255, **kwargs):
        super().__init__(**kwargs)
        self.max_length = max_length
    
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
        return value
    
    def get_sql_type(self) -> str:
        return f"VARCHAR({self.max_length})"


class TextField(Field):
    """Text field for longer strings without length limit."""
    
    def validate(self, value: Any) -> Optional[str]:
        value = super().validate(value)
        if value is None:
            return None
        return str(value)
    
    def get_sql_type(self) -> str:
        return "TEXT"


class FloatField(Field):
    """Float/decimal field type."""
    
    def validate(self, value: Any) -> Optional[float]:
        value = super().validate(value)
        if value is None:
            return None
        if not isinstance(value, (int, float)):
            try:
                return float(value)
            except (ValueError, TypeError):
                raise ValueError(f"Field '{self.name}' must be a number")
        return float(value)
    
    def get_sql_type(self) -> str:
        return "REAL"


class BooleanField(Field):
    """Boolean field type."""
    
    def __init__(self, default: bool = False, **kwargs):
        super().__init__(default=default, **kwargs)
    
    def validate(self, value: Any) -> Optional[bool]:
        value = super().validate(value)
        if value is None:
            return None
        return bool(value)
    
    def get_sql_type(self) -> str:
        return "BOOLEAN"


class DateTimeField(Field):
    """DateTime field type."""
    
    def __init__(self, auto_now: bool = False, auto_now_add: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
    
    def validate(self, value: Any) -> Optional[datetime]:
        value = super().validate(value)
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                raise ValueError(
                    f"Field '{self.name}' must be a valid datetime string"
                )
        raise ValueError(f"Field '{self.name}' must be a datetime")
    
    def get_sql_type(self) -> str:
        return "DATETIME"


class DateField(Field):
    """Date field type."""
    
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
                raise ValueError(f"Field '{self.name}' must be a valid date string")
        raise ValueError(f"Field '{self.name}' must be a date")
    
    def get_sql_type(self) -> str:
        return "DATE"


class ForeignKey(Field):
    """Foreign key field for relationships."""
    
    def __init__(self, to: str, on_delete: str = "CASCADE", **kwargs):
        super().__init__(**kwargs)
        self.to = to
        self.on_delete = on_delete
    
    def validate(self, value: Any) -> Optional[int]:
        value = super().validate(value)
        if value is None:
            return None
        if not isinstance(value, int):
            try:
                return int(value)
            except (ValueError, TypeError):
                raise ValueError(f"Field '{self.name}' must be an integer (foreign key)")
        return value
    
    def get_sql_type(self) -> str:
        return "INTEGER"
    
    def get_column_definition(self) -> str:
        base = super().get_column_definition()
        return f"{base} REFERENCES {self.to}(id) ON DELETE {self.on_delete}"
