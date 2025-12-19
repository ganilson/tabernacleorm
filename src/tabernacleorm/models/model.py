"""
Base Model class for TabernacleORM.
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from ..core.connection import get_connection
from ..fields.base import Field
from .meta import ModelMeta
from .hooks import HookMixin


class Model(HookMixin, metaclass=ModelMeta):
    """
    Base class for all models.
    
    Provides CRUD operations, validation, and hook integration.
    """
    
    # Config options (override in subclasses)
    __collection__: str
    __engine__: Optional[str] = None  # Force specific engine
    
    def __init__(self, **kwargs):
        self._modified_fields = set()
        self._is_new = True
        
        # Initialize fields with defaults
        for name, field in self._fields.items():
            if name in kwargs:
                setattr(self, name, kwargs[name])
            else:
                # Set default directly to avoid marking as modified
                # Store in __dict__ so descriptors can find it
                default = field.get_default()
                self.__dict__[name] = default
    
    def __repr__(self) -> str:
        try:
            return f"<{self.__class__.__name__}: {self.id}>"
        except Exception:
            return f"<{self.__class__.__name__}>"

    
    @property
    def is_new(self) -> bool:
        """True if document has not been saved yet."""
        return self._is_new
    
    @property
    def id(self) -> Any:
        """Get ID (alias for primary key)."""
        pk_field = self._primary_key
        if pk_field == "id":
            return self.__dict__.get("id")
        return getattr(self, pk_field)
    
    @id.setter
    def id(self, value: Any):
        """Set ID."""
        pk_field = self._primary_key
        if pk_field == "id":
            self.__dict__["id"] = value
        else:
            setattr(self, pk_field, value)
    
    def is_modified(self, field: str) -> bool:
        """Check if a field has been modified."""
        return field in self._modified_fields
    
    def get_changes(self) -> Dict[str, Any]:
        """Get dictionary of modified fields and their new values."""
        return {
            field: getattr(self, field)
            for field in self._modified_fields
        }
    
    def to_dict(self, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
        """Convert model to dictionary."""
        data = {}
        exclude = exclude or []
        for name, field in self._fields.items():
            if name in exclude:
                continue
            value = getattr(self, name)
            # Basic serialization logic available in field.to_db usually handles this,
            # but to_dict might want a python-native dict.
            # For now return as-is or serialized? Usually to_dict returns serializable data.
            data[name] = field.to_db(value)
        return data
    
    @classmethod
    def find(cls, query: Optional[Dict[str, Any]] = None) -> "QuerySet":
        """
        Start a query.
        
        Args:
            query: Optional filter conditions
            
        Returns:
            QuerySet instance
        """
        from ..query.queryset import QuerySet
        qs = QuerySet(cls)
        if query:
            qs = qs.filter(query)
        return qs
    
    @classmethod
    async def findOne(cls, query: Dict[str, Any]) -> Optional["Model"]:
        """Find a single document."""
        return await cls.find(query).first()
    
    @classmethod
    async def findById(cls, id: Any) -> Optional["Model"]:
        """Find a document by ID."""
        return await cls.find({"id": id}).first()
    
    @classmethod
    async def create(cls, **kwargs) -> "Model":
        """Create and save a new document."""
        instance = cls(**kwargs)
        await instance.save()
        return instance
    
    async def save(self) -> None:
        """Save the document (insert or update)."""
        # Run pre-validation hooks
        await self._run_hooks("pre_validate")
        
        # Validate all fields
        self.validate()
        
        # Run post-validation hooks
        await self._run_hooks("post_validate")
        
        # Run pre-save hooks
        await self._run_hooks("pre_save")
        
        db = self._get_db()
        collection = self.__collection__
        
        data = self._to_db_data()
        
        if self._is_new:
            # Insert
            await self._run_hooks("pre_insert")
            
            # If ID is set, allow it (for custom UUIDs/IDs)
            # If not, let DB handle it (auto-increment/ObjectId)
            
            new_id = await db.insertOne(collection, data)
            
            if new_id is not None:
                # Update ID on instance
                # We need to handle engine-specific ID normalization
                 # denormalizeId expects ID from DB and potentially converts it
                 # For example ObjectId -> str
                 normalized_id = db.denormalizeId(new_id)
                 setattr(self, "id", normalized_id)
            
            self._is_new = False
            self._modified_fields.clear()
            
            await self._run_hooks("post_insert")
        else:
            # Update
            await self._run_hooks("pre_update")
            
            # Only update modified fields
            if self._modified_fields:
                update_data = {
                    k: data[k] for k in self._modified_fields
                    if k != "id"  # Never update ID
                }
                
                if update_data:
                    query = {"id": self.id}
                    await db.updateOne(collection, query, {"$set": update_data})
            
            self._modified_fields.clear()
            
            await self._run_hooks("post_update")
            
        await self._run_hooks("post_save")
    
    async def delete(self) -> None:
        """Delete the document."""
        if self._is_new:
            return
            
        await self._run_hooks("pre_delete")
        
        db = self._get_db()
        await db.deleteOne(self.__collection__, {"id": self.id})
        
        await self._run_hooks("post_delete")
        self._is_new = True  # Mark as new if deleted (so it could be re-saved as new)
    
    def validate(self) -> None:
        """Validate all fields."""
        for name, field in self._fields.items():
            value = getattr(self, name)
            field.validate(value)
    
    def _to_db_data(self) -> Dict[str, Any]:
        """Convert fields to DB storage format."""
        data = {}
        for name, field in self._fields.items():
            value = getattr(self, name)
            data[name] = field.to_db(value)
        return data
    
    @classmethod
    async def insertMany(
        cls,
        documents: List[Union["Model", Dict[str, Any]]],
        batch_size: int = 100
    ) -> List[Any]:
        """Insert multiple documents."""
        # TODO: Handle Model instances vs dicts
        # For now assume dicts or Model instances that need serialization
        raw_docs = []
        for doc in documents:
            if isinstance(doc, Model):
                doc.validate()
                raw_docs.append(doc._to_db_data())
            else:
                raw_docs.append(doc)
        
        db = cls._get_db()
        ids = await db.insertMany(cls.__collection__, raw_docs, batch_size)
        return [db.denormalizeId(i) for i in ids]
    
    @classmethod
    async def updateMany(
        cls,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """Update multiple documents."""
        db = cls._get_db()
        return await db.updateMany(cls.__collection__, query, update)
    
    @classmethod
    async def deleteMany(cls, query: Dict[str, Any]) -> int:
        """Delete multiple documents."""
        db = cls._get_db()
        return await db.deleteMany(cls.__collection__, query)
    
    @classmethod
    async def count(cls, query: Optional[Dict[str, Any]] = None) -> int:
        """Count documents."""
        db = cls._get_db()
        return await db.count(cls.__collection__, query or {})
    
    @classmethod
    async def aggregate(cls, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run aggregation pipeline."""
        db = cls._get_db()
        return await db.aggregate(cls.__collection__, pipeline)
    
    @classmethod
    def _get_db(cls):
        """Get database connection."""
        conn = get_connection()
        if not conn or not conn.is_connected:
            raise RuntimeError("Database not connected")
        
        # Determine engine
        # If model has specific engine defined, use that?
        # For now use the connection's default logic
        return conn.engine


class EmbeddedModel(Model):
    """
    Model meant to be embedded in another document.
    Does not have a collection or direct CRUD (save/delete).
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Embedded models don't have _is_new tracking in the same way
        # But fields still track modifications
    
    async def save(self):
        raise NotImplementedError("EmbeddedModel cannot be saved directly")
    
    async def delete(self):
        raise NotImplementedError("EmbeddedModel cannot be deleted directly")
