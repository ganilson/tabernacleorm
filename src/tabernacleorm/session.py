from typing import Any, Dict, List, Optional, Tuple, Type, TYPE_CHECKING
from contextlib import asynccontextmanager

if TYPE_CHECKING:
    from .engines.base import BaseEngine

class Session:
    """
    Represents a database session with a specific connection/transaction scope.
    """
    
    def __init__(self, engine: "BaseEngine", connection: Any):
        self.engine = engine
        self.connection = connection
        self._in_transaction = False

    # ==================== CRUD Operations ====================
    
    async def insertOne(
        self,
        collection: str,
        document: Dict[str, Any]
    ) -> Any:
        return await self.engine.insertOne(collection, document, _connection=self.connection)
    
    async def insertMany(
        self,
        collection: str,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> List[Any]:
        return await self.engine.insertMany(collection, documents, batch_size, _connection=self.connection)
    
    async def findOne(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        return await self.engine.findOne(collection, query, projection, _connection=self.connection)
    
    async def findMany(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[List[str]] = None,
        sort: Optional[List[Tuple[str, int]]] = None,
        skip: int = 0,
        limit: int = 0
    ) -> List[Dict[str, Any]]:
        return await self.engine.findMany(
            collection, query, projection, sort, skip, limit, _connection=self.connection
        )
    
    async def updateOne(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> int:
        return await self.engine.updateOne(collection, query, update, upsert, _connection=self.connection)
    
    async def updateMany(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        return await self.engine.updateMany(collection, query, update, _connection=self.connection)
    
    async def deleteOne(
        self,
        collection: str,
        query: Dict[str, Any]
    ) -> int:
        return await self.engine.deleteOne(collection, query, _connection=self.connection)
    
    async def deleteMany(
        self,
        collection: str,
        query: Dict[str, Any]
    ) -> int:
        return await self.engine.deleteMany(collection, query, _connection=self.connection)
    
    async def count(
        self,
        collection: str,
        query: Dict[str, Any]
    ) -> int:
        return await self.engine.count(collection, query, _connection=self.connection)
    
    async def aggregate(
        self,
        collection: str,
        pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return await self.engine.aggregate(collection, pipeline, _connection=self.connection)
    
    # ==================== Transaction Control ====================

    async def commit(self):
        """Commit the transaction associated with this session."""
        if self._in_transaction:
            await self.engine.commitTransaction(self.connection)
            self._in_transaction = False

    async def rollback(self):
        """Rollback the transaction associated with this session."""
        if self._in_transaction:
            await self.engine.rollbackTransaction(self.connection)
            self._in_transaction = False
