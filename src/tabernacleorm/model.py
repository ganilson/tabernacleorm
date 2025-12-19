"""
Base Model class for TabernacleORM.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar
from datetime import datetime
from .fields import Field, IntegerField, DateTimeField
from .query import QuerySet

T = TypeVar("T", bound="Model")


class ModelMeta(type):
    """Metaclass for Model to collect field definitions."""
    
    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        cls = super().__new__(mcs, name, bases, namespace)
        
        # Collect fields from current class
        fields = {}
        for key, value in namespace.items():
            if isinstance(value, Field):
                value.name = key
                fields[key] = value
        
        # Inherit fields from parent classes
        for base in bases:
            if hasattr(base, "_fields"):
                for key, value in base._fields.items():
                    if key not in fields:
                        # Create a copy reference with the correct name
                        value.name = key
                        fields[key] = value
        
        cls._fields = fields
        
        return cls


class Model(metaclass=ModelMeta):
    """Base model class for all ORM models."""
    
    id = IntegerField(primary_key=True, auto_increment=True)
    
    _table_name: Optional[str] = None
    _db: Optional["Database"] = None
    
    def __init__(self, **kwargs):
        # Set default values first (bypass validation by using __dict__)
        for name, field in self._fields.items():
            if field.default is not None:
                self.__dict__[name] = field.default
            else:
                self.__dict__[name] = None
        
        # Handle auto_now_add for DateTimeField
        for name, field in self._fields.items():
            if isinstance(field, DateTimeField) and field.auto_now_add:
                self.__dict__[name] = datetime.now()
        
        # Set provided values (this WILL validate)
        for key, value in kwargs.items():
            if key in self._fields:
                setattr(self, key, value)
            else:
                raise AttributeError(
                    f"'{self.__class__.__name__}' has no field '{key}'"
                )
    
    def __repr__(self) -> str:
        pk_value = getattr(self, "id", None)
        return f"<{self.__class__.__name__}(id={pk_value})>"
    
    @classmethod
    def get_table_name(cls) -> str:
        """Get the table name for this model."""
        if cls._table_name:
            return cls._table_name
        return cls.__name__.lower() + "s"
    
    @classmethod
    def set_database(cls, db: "Database") -> None:
        """Set the database instance for this model."""
        cls._db = db
        db.register_model(cls)
    
    @classmethod
    def get_database(cls) -> "Database":
        """Get the database instance."""
        if cls._db is None:
            from .database import Database
            cls._db = Database.get_instance()
        if cls._db is None:
            raise RuntimeError("No database configured. Call Model.set_database() first.")
        return cls._db
    
    @classmethod
    def get_create_table_sql(cls) -> str:
        """Generate CREATE TABLE SQL statement."""
        columns = []
        for name, field in cls._fields.items():
            columns.append(field.get_column_definition())
        
        table_name = cls.get_table_name()
        columns_sql = ",\n    ".join(columns)
        return f"CREATE TABLE IF NOT EXISTS {table_name} (\n    {columns_sql}\n)"
    
    @classmethod
    def all(cls: Type[T]) -> QuerySet[T]:
        """Get all records."""
        return QuerySet(cls)
    
    @classmethod
    def filter(cls: Type[T], **kwargs) -> QuerySet[T]:
        """Filter records by field values."""
        return QuerySet(cls).filter(**kwargs)
    
    @classmethod
    def get(cls: Type[T], **kwargs) -> Optional[T]:
        """Get a single record by field values."""
        return QuerySet(cls).filter(**kwargs).first()
    
    @classmethod
    def get_by_id(cls: Type[T], id: int) -> Optional[T]:
        """Get a record by primary key."""
        return cls.get(id=id)
    
    @classmethod
    def create(cls: Type[T], **kwargs) -> T:
        """Create and save a new record."""
        instance = cls(**kwargs)
        instance.save()
        return instance
    
    def save(self) -> None:
        """Save the model instance to the database."""
        db = self.get_database()
        
        # Handle auto_now for DateTimeField
        for name, field in self._fields.items():
            if isinstance(field, DateTimeField) and field.auto_now:
                setattr(self, name, datetime.now())
        
        if self.id is None:
            self._insert(db)
        else:
            self._update(db)
    
    def _insert(self, db: "Database") -> None:
        """Insert a new record."""
        fields = []
        values = []
        placeholders = []
        
        for name, field in self._fields.items():
            if name == "id" and field.primary_key:
                continue  # Skip auto-increment primary key
            
            value = getattr(self, name)
            if value is not None or not field.nullable:
                fields.append(name)
                values.append(self._serialize_value(value))
                placeholders.append("?")
        
        table_name = self.get_table_name()
        fields_sql = ", ".join(fields)
        placeholders_sql = ", ".join(placeholders)
        
        sql = f"INSERT INTO {table_name} ({fields_sql}) VALUES ({placeholders_sql})"
        db.execute(sql, tuple(values))
        
        # Get the inserted ID
        self.id = db.last_insert_id()
    
    def _update(self, db: "Database") -> None:
        """Update an existing record."""
        sets = []
        values = []
        
        for name, field in self._fields.items():
            if name == "id":
                continue
            
            value = getattr(self, name)
            sets.append(f"{name} = ?")
            values.append(self._serialize_value(value))
        
        values.append(self.id)
        
        table_name = self.get_table_name()
        sets_sql = ", ".join(sets)
        
        sql = f"UPDATE {table_name} SET {sets_sql} WHERE id = ?"
        db.execute(sql, tuple(values))
    
    def delete(self) -> None:
        """Delete the model instance from the database."""
        if self.id is None:
            raise ValueError("Cannot delete unsaved instance")
        
        db = self.get_database()
        table_name = self.get_table_name()
        
        sql = f"DELETE FROM {table_name} WHERE id = ?"
        db.execute(sql, (self.id,))
        self.id = None
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize a value for database storage."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, bool):
            return 1 if value else 0
        return value
    
    @classmethod
    def _deserialize_row(cls: Type[T], row: Any) -> T:
        """Deserialize a database row into a model instance."""
        data = dict(row)
        instance = cls.__new__(cls)
        
        for name, field in cls._fields.items():
            if name in data:
                value = data[name]
                # Convert stored value back to Python type
                if isinstance(field, DateTimeField) and value:
                    value = datetime.fromisoformat(value)
                setattr(instance, name, value)
            else:
                setattr(instance, name, field.default)
        
        return instance
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {name: getattr(self, name) for name in self._fields}
    
    def refresh(self) -> None:
        """Reload the instance from the database."""
        if self.id is None:
            raise ValueError("Cannot refresh unsaved instance")
        
        fresh = self.get_by_id(self.id)
        if fresh is None:
            raise ValueError("Instance no longer exists in database")
        
        for name in self._fields:
            setattr(self, name, getattr(fresh, name))
