"""
TabernacleORM - A universal Python ORM for MongoDB, PostgreSQL, MySQL, and SQLite.

Inspired by Mongoose, designed for FastAPI and modern Python applications.
"""

from .core.connection import connect, disconnect, get_connection
from .core.config import Config
from .models.model import Model, EmbeddedModel
from .fields import (
    Field,
    IntegerField,
    StringField,
    TextField,
    FloatField,
    BooleanField,
    DateTimeField,
    DateField,
    UUIDField,
    JSONField,
    ArrayField,
    ForeignKey,
    OneToMany,
    ManyToMany,
    EmbeddedField,
)
from .query.queryset import QuerySet
from .models.hooks import hook

__version__ = "2.1.2"
__author__ = "Ganilson Garcia"
__all__ = [
    # Connection
    "connect",
    "disconnect",
    "get_connection",
    "Config",
    # Models
    "Model",
    "EmbeddedModel",
    # Fields
    "Field",
    "IntegerField",
    "StringField",
    "TextField",
    "FloatField",
    "BooleanField",
    "DateTimeField",
    "DateField",
    "UUIDField",
    "JSONField",
    "ArrayField",
    "ForeignKey",
    "OneToMany",
    "ManyToMany",
    "EmbeddedField",
    # Query
    "QuerySet",
    # Hooks
    "hook",
]
