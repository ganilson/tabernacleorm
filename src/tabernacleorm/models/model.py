"""
Base Model class for TabernacleORM.
Fully async, Pydantic-based, with support for advanced ORM features.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union, ClassVar, Coroutine, Tuple
from datetime import datetime
from pydantic import BaseModel, Field as PydanticField
from pydantic.fields import FieldInfo
from pydantic._internal._model_construction import ModelMetaclass as PydanticMetaclass
from ..fields import Field, Relationship, RelationshipInfo
from ..query.queryset import QuerySet
from ..core.connection import get_connection

T = TypeVar("T", bound="Model")

class ColumnExpression:
    """Represents a column in a query expression."""
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other): return ("$eq", self.name, other)
    def __ne__(self, other): return ("$ne", self.name, other)
    def __gt__(self, other): return ("$gt", self.name, other)
    def __ge__(self, other): return ("$gte", self.name, other)
    def __lt__(self, other): return ("$lt", self.name, other)
    def __le__(self, other): return ("$lte", self.name, other)
    def in_(self, other): return ("$in", self.name, other)
    def like(self, other): return ("$like", self.name, other)

class ModelMetaclass(PydanticMetaclass):
    """Metaclass to handle ORM metadata and Query Expressions."""
    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)
        
        # Register Model globally
        from ..core.registry import register_model
        register_model(name, cls)

        # Build _tabernacle_meta from Pydantic fields
        cls._tabernacle_meta = {
            "table_name": cls.__name__.lower() + "s",  # customized via Config if needed
            "primary_key": None,
            "columns": {},
            "relationships": {}
        }
        
        # Check explicit Config for table name override (Pydantic V2 uses class Config or model_config)
        # We look for a nested Config class standard in standard ORMs or Pydantic V1 compat
        if hasattr(cls, "Config") and hasattr(cls.Config, "table_name"):
            cls._tabernacle_meta["table_name"] = cls.Config.table_name

        for parser_field_name, field_info in cls.model_fields.items():
            extra = field_info.json_schema_extra or {}
            
            # Handle Relationships
            if "relationship" in extra:
                rel_info = extra["relationship"]
                cls._tabernacle_meta["relationships"][parser_field_name] = rel_info
                continue
            
            # Handle Columns
            # If explicit Field() was used with our wrapper, 'tabernacle_args' exists.
            # If simple type hint was used, we assume standard column.
            tab_args = extra.get("tabernacle_args", {})
            cls._tabernacle_meta["columns"][parser_field_name] = tab_args
            
            if tab_args.get("primary_key"):
                cls._tabernacle_meta["primary_key"] = parser_field_name
            
            # Install Query Proxy on the class
            if parser_field_name not in namespace:
                setattr(cls, parser_field_name, ColumnExpression(parser_field_name))

class Model(BaseModel, metaclass=ModelMetaclass):
    """
    Base ORM Model compatible with Pydantic and Tabernacle Engines.
    """
    # Internal state
    _persisted: bool = False
    _connection_override: Any = None # For session support

    def __init__(self, **data):
        super().__init__(**data)
        # Mark as persisted if ID is present
        pk = self.get_pk_field()
        if pk and getattr(self, pk) is not None:
             self._persisted = True

    @classmethod
    def get_pk_field(cls) -> Optional[str]:
        return cls._tabernacle_meta["primary_key"]

    @classmethod
    def get_table_name(cls) -> str:
        return cls._tabernacle_meta["table_name"]

    @classmethod
    def get_engine(cls):
        """Get the active engine."""
        conn = get_connection()
        if not conn or not conn.engine:
            raise RuntimeError("Database not connected. Call connect() first.")
        # Support read/write splitting conceptually here if needed
        return conn.engine

    # ----- Query API -----

    @classmethod
    def all(cls: Type[T]) -> QuerySet[T]:
        return QuerySet(cls)

    @classmethod
    def filter(cls: Type[T], *args, **kwargs) -> QuerySet[T]:
        qs = QuerySet(cls)
        if args:
            qs = qs.filter_expr(*args)
        if kwargs:
            qs = qs.filter(**kwargs)
        return qs

    @classmethod
    def get(cls: Type[T], **kwargs) -> Coroutine[Any, Any, Optional[T]]:
        return cls.filter(**kwargs).first()

    @classmethod
    def create(cls: Type[T], **kwargs) -> Coroutine[Any, Any, T]:
        async def _create():
            instance = cls(**kwargs)
            await instance.save()
            return instance
        return _create()

    # ----- CRUD -----

    async def save(self, session: Any = None) -> None:
        """Save the object (Insert or Update)."""
        is_create = not self._persisted
        
        await self.before_save()
        if is_create:
            await self.before_create()
        
        # Determine engine or session connection
        engine = self.get_engine()
        session_conn = None
        if session:
            # Assumes session object has 'connection' attribute
            if hasattr(session, "connection"):
                session_conn = session.connection
            else:
                session_conn = session # Raw connection passed?

        conn_arg = {"_connection": session_conn} if session_conn else {}
        
        data = self.model_dump(exclude_unset=True)
        cleaned = {}
        pk = self.get_pk_field()
        
        for k, v in data.items():
            if k in self._tabernacle_meta["relationships"]:
                continue
            if k == pk and v is None and is_create:
                continue
            cleaned[k] = v

        if is_create:
            new_id = await engine.insertOne(self.get_table_name(), cleaned, **conn_arg)
            if pk:
                # If engine returns ID (string or int), set it
                # Ensure type matches field annotation? Pydantic validation handles assignment?
                # We bypass validation for speed or re-validate
                setattr(self, pk, new_id)
            self._persisted = True
            await self.after_create()
        else:
            if not pk:
                raise ValueError("Cannot update model without primary key.")
            query = {pk: getattr(self, pk)}
            await engine.updateOne(self.get_table_name(), query, cleaned, **conn_arg)
        
        await self.after_save()

    async def delete(self, session: Any = None) -> None:
        """Delete from DB."""
        if not self._persisted:
            return
        
        await self.before_delete()
        
        engine = self.get_engine()
        session_conn = session.connection if session and hasattr(session, "connection") else session
        conn_arg = {"_connection": session_conn} if session_conn else {}

        pk = self.get_pk_field()
        query = {pk: getattr(self, pk)}
        
        await engine.deleteOne(self.get_table_name(), query, **conn_arg)
        self._persisted = False
        
        await self.after_delete()

    @classmethod
    def _resolve_model(cls, model_ref: Any) -> Type["Model"]:
        """Resolve string model reference to class."""
        if isinstance(model_ref, type) and issubclass(model_ref, Model):
            return model_ref
        if isinstance(model_ref, str):
            # Simple resolution: look in same module or global registry
            # For now, require it to be imported/available or use registry
            # minimal implementation: check globals of the defining module?
            # Better: use a global ORM registry. 
            from ..core.registry import get_model
            m = get_model(model_ref)
            if m: return m
        raise ValueError(f"Could not resolve model '{model_ref}'")

    async def fetch_related(self, field_name: str) -> Any:
        """
        Lazy load a relationship.
        e.g. posts = await user.fetch_related("posts")
        """
        meta = self._tabernacle_meta
        if field_name not in meta["relationships"]:
             raise AttributeError(f"'{field_name}' is not a registered relationship on {self.__class__.__name__}")
        
        rel_info = meta["relationships"][field_name]
        # rel_info is a RelationshipInfo object
        
        target_model = self._resolve_model(rel_info.link_model)
        
        # Determine relationship type
        # 1. OneToMany (Reverse of FK)
        #    Target model should have a FK pointing to us.
        #    We need the field name on Target that points to us.
        
        # If back_populates is explicit:
        remote_field = rel_info.back_populates
        
        # Heuristic if not explicit:
        if not remote_field:
            # Assume target has 'user_id' if we are 'User'
            remote_field = f"{self.__class__.__name__.lower()}_id"
            
        # Check if it's ManyToMany (TODO) or OneToMany
        # For now assume OneToMany for list results
        
        # Check if target has this field
        # If target has a ForeignKey pointing to us, it's OneToMany
        # If we have a ForeignKey pointing to target, it's ManyToOne (belongs_to)
        
        # Case A: We have a FK pointing to them (ManyToOne/OneToOne)
        # Check if 'field_name' corresponds to a local FK column? 
        # Usually Relationships are virtual. The FK column is 'author_id', relation is 'author'.
        
        # Check internal columns for FK
        my_fk = None
        for col_name, col_args in meta["columns"].items():
            if col_args.get("foreign_key") == target_model.__name__: # or match table?
                # This logic is fuzzy without stricter definitions. 
                # Let's rely on naming convention: field_name + "_id"
                if f"{field_name}_id" == col_name or field_name == col_name.replace("_id",""):
                     my_fk = col_name
                     break
        
        # If we found a local FK, it's a BelongsTo
        if hasattr(self, f"{field_name}_id"):
             fk_val = getattr(self, f"{field_name}_id")
             if fk_val is None: return None
             return await target_model.get(id=fk_val)

        # Case B: OneToMany (They point to us)
        # We query Target where target.remote_field == self.id
        # Verify target has that field
        # We can try to query.
        pk = self.get_pk_field()
        my_id = getattr(self, pk)
        
        return await target_model.filter({remote_field: my_id}).all()
    async def before_save(self): pass
    async def after_save(self): pass
    async def before_create(self): pass
    async def after_create(self): pass
    async def before_delete(self): pass
    async def after_delete(self): pass

class EmbeddedModel(BaseModel):
    """Simple embedded model for NoSQL usage."""
    pass
