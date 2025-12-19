"""
Relationship fields for TabernacleORM.
"""

from typing import Any, Optional, Type, Union, List

from .base import Field


class ForeignKey(Field):
    """
    Many-to-One relationship.
    
    Stores the ID of the related model.
    """
    
    _field_type = "foreign_key"
    
    def __init__(
        self,
        to: Union[Type, str],
        *,
        on_delete: str = "CASCADE",
        on_update: str = "CASCADE",
        related_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.to = to
        self.on_delete = on_delete.upper()
        self.on_update = on_update.upper()
        self.related_name = related_name
        self._to_model = None
    
    def get_related_model(self) -> Type:
        """Resolve string model name to class."""
        if self._to_model:
            return self._to_model
        
        if isinstance(self.to, str):
            # TODO: Implement model registry to resolve string names
            # For now assume it will be resolved by the Model metaclass
            return None
        
        self._to_model = self.to
        return self._to_model
    
    def validate(self, value: Any) -> Any:
        super().validate(value)
        if value is None:
            return None
        
        # If value is a Model instance, get its ID
        if hasattr(value, "id"):
            return value.id
        
        return value
    
    def get_schema(self) -> dict:
        schema = super().get_schema()
        model = self.get_related_model()
        schema["related_model"] = model.__collection__ if model else str(self.to)
        schema["on_delete"] = self.on_delete
        schema["on_update"] = self.on_update
        return schema


class OneToMany(Field):
    """
    Reverse relationship for ForeignKey.
    does not create a column in the database.
    """
    
    def __init__(
        self,
        to: Union[Type, str],
        *,
        foreign_key: str,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.to = to
        self.foreign_key = foreign_key
    
    def __get__(self, obj: Any, objtype: Optional[Type] = None) -> Any:
        """
        Return a QuerySet context for the related items.
        
        usage: user.posts.all()
        """
        if obj is None:
            return self
        
        # Return a proxy/manager that filters the related model
        # return QuerySet(self.get_related_model()).filter({self.foreign_key: obj.id})
        pass  # Implementation handled by Model logic/QuerySet


class ManyToMany(Field):
    """
    Many-to-Many relationship.
    Creates a junction table.
    """
    
    _field_type = "many_to_many"
    
    def __init__(
        self,
        to: Union[Type, str],
        *,
        through: Optional[str] = None,
        related_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.to = to
        self.through = through
        self.related_name = related_name


class EmbeddedField(Field):
    """
    Embedded document field (for MongoDB/JSON).
    """
    
    _field_type = "embedded"
    
    def __init__(self, model: Type, **kwargs):
        super().__init__(**kwargs)
        self.embedded_model = model
    
    def validate(self, value: Any) -> Any:
        value = super().validate(value)
        if value is None:
            return None
        
        if isinstance(value, dict):
            # Convert dict to model instance
            return self.embedded_model(**value)
        
        if isinstance(value, self.embedded_model):
            return value
        
        raise ValueError(f"Field '{self.name}' must be a {self.embedded_model.__name__} instance")
    
    def to_db(self, value: Any) -> Any:
        if value is None:
            return None
        if hasattr(value, "to_dict"):
            return value.to_dict()
        return value
