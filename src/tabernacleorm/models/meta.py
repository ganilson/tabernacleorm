"""
Metaclass for TabernacleORM models.
"""

from typing import Any, Dict, Type

from ..fields.base import Field
from .hooks import HookMixin


class ModelMeta(type):
    """
    Metaclass for Model.
    
    Handles:
    1. Field collection and registration
    2. Hook collection
    3. Engine configuration inheritance
    """
    
    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        # Create class
        cls = super().__new__(mcs, name, bases, namespace)
        
        if name == "Model":
            return cls
        
        # Collect fields
        fields = {}
        primary_key = None
        
        # Inherit fields from parent classes
        for base in bases:
            if hasattr(base, "_fields"):
                for key, value in base._fields.items():
                    # Copy field to avoid sharing state between classes
                    # (This is simplified; a deep copy or re-instantiation might be needed for complex fields)
                    fields[key] = value
                    if value.primary_key:
                        primary_key = key
        
        # Collect fields from current class
        for key, value in namespace.items():
            if isinstance(value, Field):
                value.name = key
                value.model = cls
                fields[key] = value
                if value.primary_key:
                    primary_key = key
        
        cls._fields = fields
        cls._primary_key = primary_key or "id"
        
        # Collect hooks using HookMixin logic
        if issubclass(cls, HookMixin):
            cls._hooks_registry = cls._collect_hooks()
        
        # Set collection name if not present
        if not hasattr(cls, "__collection__"):
            # Default to lowercase plural class name
            cls.__collection__ = name.lower() + "s"
        
        return cls
