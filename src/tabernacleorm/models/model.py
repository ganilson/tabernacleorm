"""
Base Model class for TabernacleORM.
Fully async, Pydantic-based, with support for advanced ORM features.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, ClassVar, Coroutine, Tuple
from datetime import datetime
from pydantic import BaseModel, Field as PydanticField
from pydantic.fields import FieldInfo
from pydantic._internal._model_construction import ModelMetaclass as PydanticMetaclass
from ..fields import Field, Relationship, RelationshipInfo, IntegerField
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
        # We look for a nested Config class or model_config dict
        config = namespace.get("Config") or getattr(cls, "Config", None)
        model_config = namespace.get("model_config") or getattr(cls, "model_config", None)
        
        if config and hasattr(config, "table_name"):
            cls._tabernacle_meta["table_name"] = getattr(config, "table_name")
        elif model_config and isinstance(model_config, dict) and "table_name" in model_config:
            cls._tabernacle_meta["table_name"] = model_config["table_name"]
        elif hasattr(cls, "Config") and hasattr(cls.Config, "table_name"):
            # Fallback for inherited Config
            cls._tabernacle_meta["table_name"] = cls.Config.table_name

        # Auto-add 'id' field if not present in annotation
        # Pydantic way involves adding to model_fields or annotations before base init?
        # But we are in __init__.
        # Simplest: if 'id' not in annotations, add it?
        # But Pydantic V2 is strict.
        # User implies inheritance provides it?
        # Let's check Model class. It inherits BaseModel.
        # If we want an auto-ID, Model clss should have it?
        # Let's check Model definition.
        
        # We can dynamically add 'id' to _tabernacle_meta['columns'] even if not in Pydantic fields
        # BUT then save() / load() logic needs to handle it.
        # Pydantic needs 'id' field to hold the value.
        
        # Best approach: Add `id: Optional[int] = Field(default=None, primary_key=True)` to `Model` base class.
        pass

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
    # Flexible ID field that works with both SQL (int) and NoSQL (str) engines
    id: Optional[Union[int, str]] = IntegerField(primary_key=True, auto_increment=True, default=None)

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
    def find(cls: Type[T], query: Optional[Dict[str, Any]] = None, **kwargs) -> QuerySet[T]:
        """Find documents matching query."""
        qs = QuerySet(cls)
        if query:
            qs = qs.filter(query)
        if kwargs:
            qs = qs.filter(**kwargs)
        return qs

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
        
    @classmethod
    async def deleteMany(cls, query: Dict[str, Any]) -> int:
        """Delete multiple documents matching query."""
        db = cls.get_engine()
        return await db.deleteMany(cls.get_table_name(), query)
        
    @classmethod
    async def updateMany(cls, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update multiple documents matching query."""
        db = cls.get_engine()
        return await db.updateMany(cls.get_table_name(), query, update)
        
    @classmethod
    async def aggregate(cls, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run aggregation pipeline."""
        db = cls.get_engine()
        return await db.aggregate(cls.get_table_name(), pipeline)

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
        
        # Handle auto_now and auto_now_add
        for field_name, field_info in self.model_fields.items():
            extra = field_info.json_schema_extra or {}
            tab_args = extra.get("tabernacle_args", {})
            if is_create:
                if tab_args.get("auto_now_add") or tab_args.get("auto_now"):
                    if getattr(self, field_name) is None:
                        setattr(self, field_name, datetime.now())
            elif not is_create and tab_args.get("auto_now"):
                setattr(self, field_name, datetime.now())
                
        data = self.model_dump(exclude_unset=False) # Always dump to include auto-fields
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
    @classmethod
    def get_create_table_sql(cls) -> str:
        """Generate SQL to create table for this model."""
        # This is a bit tricky because SQL generation depends on dialect (Postgres vs MySQL vs SQLite)
        #Ideally, we ask the engine to generate it.
        # But for now, we provide a generic SQL generation helper OR delegate to engine.
        # Let's delegate to a new engine method `generateCreateTableSQL`.
        # This requires engine support.
        
        # Simplified: Return a structure the engine can use, or string.
        # Let's construct a schema dict and pass it to engine.createCollection logic
        
        # Actually, let's look at BaseEngine.createCollection. It takes a schema dict?
        # No, createCollection(name, schema) is there.
        # So we don't return SQL string directly to user usually, unless debug.
        # But user code has executeRaw(User.get_create_table_sql()).
        # Let's support that by asking the connected engine.
        
        engine = cls.get_engine()
        # We need to construct a generic schema definition from _tabernacle_meta
        meta = cls._tabernacle_meta
        columns = []
        for name, args in meta["columns"].items():
            col_type = args.get("sa_type", "TEXT")
            # Enhance type mapping if needed
            
            definition = {"name": name, "type": col_type}
            if args.get("primary_key"): definition["primary_key"] = True
            if args.get("nullable") is False: definition["nullable"] = False
            if args.get("unique"): definition["unique"] = True
            if args.get("default") is not None: definition["default"] = args["default"]
            if args.get("foreign_key"): definition["foreign_key"] = args["foreign_key"]
            
            columns.append(definition)
            
        return engine.generateCreateTableSQL(meta["table_name"], columns)

    @classmethod
    async def create_table(cls, safe: bool = True):
        """Create table in DB."""
        sql = cls.get_create_table_sql()
        if not sql:
            return

        engine = cls.get_engine()
        # Wrap in try/except if safe=True to ignore "exists" error, or adding IF NOT EXISTS in SQL
        if safe and "IF NOT EXISTS" not in sql.upper():
             # Basic injection, dependent on dialect
             # Better: check existence first
             if await engine.collectionExists(cls.get_table_name()):
                 return
        
        await engine.executeRaw(sql)

    async def before_save(self): pass
    async def after_save(self): pass
    async def before_create(self): pass
    async def after_create(self): pass
    async def before_delete(self): pass
    async def after_delete(self): pass

class EmbeddedModel(BaseModel):
    """Simple embedded model for NoSQL usage."""
    pass
