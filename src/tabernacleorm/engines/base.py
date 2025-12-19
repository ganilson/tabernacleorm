"""
Base engine interface for TabernacleORM.

All database engines must implement this abstract interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from contextlib import asynccontextmanager


class BaseEngine(ABC):
    """
    Abstract base class for database engines.
    
    All database-specific implementations must inherit from this class
    and implement all abstract methods.
    """
    
    def __init__(self, config):
        self.config = config
        self._connection = None
        self._connected = False
    
    # ==================== Connection ====================
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the database."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close the database connection."""
        pass
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to database."""
        return self._connected
    
    # ==================== CRUD Operations ====================
    
    @abstractmethod
    async def insertOne(
        self,
        collection: str,
        document: Dict[str, Any]
    ) -> Any:
        """
        Insert a single document.
        
        Args:
            collection: Collection/table name
            document: Document to insert
            
        Returns:
            Inserted document ID
        """
        pass
    
    @abstractmethod
    async def insertMany(
        self,
        collection: str,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> List[Any]:
        """
        Insert multiple documents.
        
        Args:
            collection: Collection/table name
            documents: Documents to insert
            batch_size: Batch size for bulk operations
            
        Returns:
            List of inserted document IDs
        """
        pass
    
    @abstractmethod
    async def findOne(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find a single document.
        
        Args:
            collection: Collection/table name
            query: Query filter
            projection: Fields to include
            
        Returns:
            Document or None
        """
        pass
    
    @abstractmethod
    async def findMany(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[List[str]] = None,
        sort: Optional[List[Tuple[str, int]]] = None,
        skip: int = 0,
        limit: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents.
        
        Args:
            collection: Collection/table name
            query: Query filter
            projection: Fields to include
            sort: Sort order [(field, direction), ...]
            skip: Number of documents to skip
            limit: Maximum documents to return (0 = no limit)
            
        Returns:
            List of documents
        """
        pass
    
    @abstractmethod
    async def updateOne(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> int:
        """
        Update a single document.
        
        Args:
            collection: Collection/table name
            query: Query filter
            update: Update operations
            upsert: Create if not exists
            
        Returns:
            Number of modified documents
        """
        pass
    
    @abstractmethod
    async def updateMany(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """
        Update multiple documents.
        
        Args:
            collection: Collection/table name
            query: Query filter
            update: Update operations
            
        Returns:
            Number of modified documents
        """
        pass
    
    @abstractmethod
    async def deleteOne(
        self,
        collection: str,
        query: Dict[str, Any]
    ) -> int:
        """
        Delete a single document.
        
        Args:
            collection: Collection/table name
            query: Query filter
            
        Returns:
            Number of deleted documents
        """
        pass
    
    @abstractmethod
    async def deleteMany(
        self,
        collection: str,
        query: Dict[str, Any]
    ) -> int:
        """
        Delete multiple documents.
        
        Args:
            collection: Collection/table name
            query: Query filter
            
        Returns:
            Number of deleted documents
        """
        pass
    
    @abstractmethod
    async def count(
        self,
        collection: str,
        query: Dict[str, Any]
    ) -> int:
        """
        Count documents matching query.
        
        Args:
            collection: Collection/table name
            query: Query filter
            
        Returns:
            Document count
        """
        pass
    
    # ==================== Aggregation ====================
    
    @abstractmethod
    async def aggregate(
        self,
        collection: str,
        pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute aggregation pipeline.
        
        Args:
            collection: Collection/table name
            pipeline: Aggregation pipeline stages
            
        Returns:
            Aggregation results
        """
        pass
    
    # ==================== Schema Operations ====================
    
    @abstractmethod
    async def createCollection(
        self,
        name: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create a collection/table.
        
        Args:
            name: Collection/table name
            schema: Schema definition
        """
        pass
    
    @abstractmethod
    async def dropCollection(self, name: str) -> None:
        """
        Drop a collection/table.
        
        Args:
            name: Collection/table name
        """
        pass
    
    @abstractmethod
    async def collectionExists(self, name: str) -> bool:
        """
        Check if collection/table exists.
        
        Args:
            name: Collection/table name
            
        Returns:
            True if exists
        """
        pass
    
    # ==================== Indexes ====================
    
    @abstractmethod
    async def createIndex(
        self,
        collection: str,
        fields: List[str],
        unique: bool = False,
        name: Optional[str] = None
    ) -> str:
        """
        Create an index.
        
        Args:
            collection: Collection/table name
            fields: Fields to index
            unique: Unique index
            name: Index name
            
        Returns:
            Index name
        """
        pass
    
    @abstractmethod
    async def dropIndex(
        self,
        collection: str,
        name: str
    ) -> None:
        """
        Drop an index.
        
        Args:
            collection: Collection/table name
            name: Index name
        """
        pass
    
    # ==================== Transactions ====================
    
    @asynccontextmanager
    async def transaction(self):
        """
        Transaction context manager.
        
        Usage:
            async with engine.transaction():
                await engine.insertOne(...)
                await engine.updateOne(...)
        """
        await self._beginTransaction()
        try:
            yield self
            await self._commitTransaction()
        except Exception:
            await self._rollbackTransaction()
            raise
    
    @abstractmethod
    async def _beginTransaction(self) -> None:
        """Begin a transaction."""
        pass
    
    @abstractmethod
    async def _commitTransaction(self) -> None:
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    async def _rollbackTransaction(self) -> None:
        """Rollback the current transaction."""
        pass
    
    # ==================== Query Building ====================
    
    def buildQuery(self, conditions: Dict[str, Any]) -> Any:
        """
        Build a database-specific query from conditions.
        
        This is overridden by each engine to translate the unified
        query syntax to engine-specific format.
        """
        return conditions
    
    # ==================== Utilities ====================
    
    @abstractmethod
    async def executeRaw(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a raw query.
        
        Args:
            query: Raw query string
            params: Query parameters
            
        Returns:
            Query results
        """
        pass
    
    async def explain(
        self,
        collection: str,
        query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Explain query execution plan.
        
        Args:
            collection: Collection/table name
            query: Query to explain
            
        Returns:
            Query execution plan
        """
        raise NotImplementedError("explain() not implemented for this engine")
    
    @property
    def engineName(self) -> str:
        """Return the engine name."""
        return self.__class__.__name__.replace("Engine", "").lower()
    
    def normalizeId(self, id_value: Any) -> Any:
        """
        Normalize ID to engine-specific format.
        Override for engines with special ID handling (e.g., MongoDB ObjectId).
        """
        return id_value
    
    def denormalizeId(self, id_value: Any) -> Any:
        """
        Convert engine-specific ID to standard format.
        Override for engines with special ID handling.
        """
        return id_value

