"""
MongoDB engine implementation for TabernacleORM.
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from uuid import UUID

from .base import BaseEngine


class MongoDBEngine(BaseEngine):
    """
    MongoDB database engine.
    
    Uses motor for async connections.
    """
    
    def __init__(self, config):
        super().__init__(config)
        self._client = None
        self._db = None
    
    async def connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
        except ImportError:
            raise ImportError(
                "motor is required for MongoDB. "
                "Install with: pip install tabernacleorm[mongodb]"
            )
        
        url = self.config.url or "mongodb://localhost:27017"
        
        # Build connection options
        options = {
            "maxPoolSize": self.config.pool_size,
            "serverSelectionTimeoutMS": self.config.timeout * 1000,
            "retryWrites": self.config.retry_writes,
        }
        
        if self.config.replica_set:
            options["replicaSet"] = self.config.replica_set
        
        if self.config.auth_source:
            options["authSource"] = self.config.auth_source
        
        self._client = AsyncIOMotorClient(url, **options)
        
        # Get database name from URL or config
        db_name = self.config.database
        if not db_name and "/" in url:
            db_name = url.split("/")[-1].split("?")[0]
        if not db_name:
            db_name = "test"
        
        self._db = self._client[db_name]
        self._connected = True
        
        if self.config.echo:
            print(f"[MongoDB] Connected to {url}/{db_name}")
    
    async def disconnect(self) -> None:
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            self._connected = False

    async def acquireConnection(self) -> Any:
        return await self._client.start_session()

    async def releaseConnection(self, connection: Any) -> None:
        connection.end_session()
    

    async def insertOne(
        self,
        collection: str,
        document: Dict[str, Any],
        _connection: Any = None
    ) -> Any:
        """Insert a single document."""
        # Convert ID if present
        if "id" in document:
            document["_id"] = document.pop("id")
        
        result = await self._db[collection].insert_one(document, session=_connection)
        return str(result.inserted_id)
    
    async def insertMany(
        self,
        collection: str,
        documents: List[Dict[str, Any]],
        batch_size: int = 100,
        _connection: Any = None
    ) -> List[Any]:
        """Insert multiple documents."""
        # Handle id to _id conversion
        for doc in documents:
            if "id" in doc and doc["id"] is not None:
                doc["_id"] = doc.pop("id")
            elif "id" in doc:
                del doc["id"]
        
        result = await self._db[collection].insert_many(documents, ordered=False, session=_connection)
        return [str(id) for id in result.inserted_ids]
    
    async def findOne(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[List[str]] = None,
        _connection: Any = None
    ) -> Optional[Dict[str, Any]]:
        """Find a single document."""
        query = self._normalize_query(query)
        proj = {f: 1 for f in projection} if projection else None
        
        doc = await self._db[collection].find_one(query, projection=proj, session=_connection)
        return self._normalize_document(doc) if doc else None
    
    async def findMany(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[List[str]] = None,
        sort: Optional[List[Tuple[str, int]]] = None,
        skip: int = 0,
        limit: int = 0,
        _connection: Any = None
    ) -> List[Dict[str, Any]]:
        """Find multiple documents."""
        query = self._normalize_query(query)
        proj = {f: 1 for f in projection} if projection else None
        
        cursor = self._db[collection].find(query, projection=proj, session=_connection)
        
        if sort:
            cursor = cursor.sort(sort)
        if skip > 0:
            cursor = cursor.skip(skip)
        if limit > 0:
            cursor = cursor.limit(limit)
        
        docs = await cursor.to_list(length=limit if limit > 0 else None)
        return [self._normalize_document(doc) for doc in docs]
    
    async def updateOne(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
        _connection: Any = None
    ) -> int:
        """Update a single document."""
        query = self._normalize_query(query)
        
        # Ensure update has $set if not already an operator
        if not any(k.startswith("$") for k in update.keys()):
            update = {"$set": update}
        
        result = await self._db[collection].update_one(query, update, upsert=upsert, session=_connection)
        return result.modified_count
    
    async def updateMany(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        _connection: Any = None
    ) -> int:
        """Update multiple documents."""
        query = self._normalize_query(query)
        
        if not any(k.startswith("$") for k in update.keys()):
            update = {"$set": update}
        
        result = await self._db[collection].update_many(query, update, session=_connection)
        return result.modified_count
    
    async def deleteOne(self, collection: str, query: Dict[str, Any], _connection: Any = None) -> int:
        """Delete a single document."""
        query = self._normalize_query(query)
        result = await self._db[collection].delete_one(query, session=_connection)
        return result.deleted_count
    
    async def deleteMany(self, collection: str, query: Dict[str, Any], _connection: Any = None) -> int:
        """Delete multiple documents."""
        query = self._normalize_query(query)
        result = await self._db[collection].delete_many(query, session=_connection)
        return result.deleted_count
    
    async def count(self, collection: str, query: Dict[str, Any], _connection: Any = None) -> int:
        """Count documents matching query."""
        query = self._normalize_query(query)
        return await self._db[collection].count_documents(query, session=_connection)
    
    async def aggregate(
        self,
        collection: str,
        pipeline: List[Dict[str, Any]],
        _connection: Any = None
    ) -> List[Dict[str, Any]]:
        """Execute aggregation pipeline."""
        # Normalize id references in pipeline
        normalized_pipeline = []
        for stage in pipeline:
            normalized_stage = {}
            for key, value in stage.items():
                if key == "$match":
                    normalized_stage[key] = self._normalize_query(value)
                elif key == "$lookup":
                    lookup = dict(value)
                    if lookup.get("localField") == "id":
                        lookup["localField"] = "_id"
                    if lookup.get("foreignField") == "id":
                        lookup["foreignField"] = "_id"
                    normalized_stage[key] = lookup
                else:
                    normalized_stage[key] = value
            normalized_pipeline.append(normalized_stage)
        
        cursor = self._db[collection].aggregate(normalized_pipeline, session=_connection)
        docs = await cursor.to_list(length=None)
        return [self._normalize_document(doc) for doc in docs]
    
    async def createCollection(
        self,
        name: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a collection."""
        try:
            await self._db.create_collection(name)
        except Exception:
            pass  # Collection may already exist
        
        # Create indexes for unique fields if schema provided
        if schema:
            for field_name, field_spec in schema.items():
                if field_spec.get("unique"):
                    await self.createIndex(name, [field_name], unique=True)
                elif field_spec.get("index"):
                    await self.createIndex(name, [field_name])
    
    async def dropCollection(self, name: str) -> None:
        """Drop a collection."""
        await self._db[name].drop()
    
    async def collectionExists(self, name: str) -> bool:
        """Check if collection exists."""
        collections = await self._db.list_collection_names()
        return name in collections
    
    async def createIndex(
        self,
        collection: str,
        fields: List[str],
        unique: bool = False,
        name: Optional[str] = None
    ) -> str:
        """Create an index."""
        from pymongo import ASCENDING
        
        # Convert field list to index specification
        index_spec = [(f, ASCENDING) for f in fields]
        
        index_name = await self._db[collection].create_index(
            index_spec,
            unique=unique,
            name=name
        )
        return index_name
    
    async def dropIndex(self, collection: str, name: str) -> None:
        """Drop an index."""
        await self._db[collection].drop_index(name)
    
    async def beginTransaction(self, connection: Any) -> None:
        """Begin a transaction."""
        connection.start_transaction()
    
    async def commitTransaction(self, connection: Any) -> None:
        """Commit the current transaction."""
        await connection.commit_transaction()
        connection.end_session() # Transaction implies session life cycle here or in releaseConnection?
        # Connection is released in finally block of context manager, which calls end_session.
    
    async def rollbackTransaction(self, connection: Any) -> None:
        """Rollback the current transaction."""
        await connection.abort_transaction()
        # end_session called in releaseConnection
    
    async def executeRaw(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """Execute a raw command (for MongoDB, this runs a command)."""
        # Parse as JSON command
        import json
        try:
            command = json.loads(query)
            result = await self._db.command(command)
            return [result] if result else []
        except json.JSONDecodeError:
            raise ValueError("MongoDB raw queries must be valid JSON")
    
    async def explain(
        self,
        collection: str,
        query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Explain query execution plan."""
        query = self._normalize_query(query)
        return await self._db[collection].find(query).explain()
    
    def _normalize_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize query (convert id to _id, etc.)."""
        if not query:
            return {}
        
        normalized = {}
        for key, value in query.items():
            if key == "id":
                # Convert id to _id and handle ObjectId
                normalized["_id"] = self._to_object_id(value)
            else:
                if isinstance(value, dict):
                    normalized[key] = self._normalize_query(value)
                else:
                    normalized[key] = value
        
        return normalized
    
    def _normalize_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize document (convert _id to id, etc.)."""
        if not doc:
            return doc
        
        result = {}
        for key, value in doc.items():
            if key == "_id":
                result["id"] = str(value)
            else:
                result[key] = value
        
        return result
    
    def _to_object_id(self, value: Any) -> Any:
        """Convert value to ObjectId if it looks like one."""
        if value is None:
            return None
        
        from bson import ObjectId
        
        if isinstance(value, ObjectId):
            return value
        
        if isinstance(value, str) and len(value) == 24:
            try:
                return ObjectId(value)
            except Exception:
                return value
        
        if isinstance(value, dict):
            # Handle operators like $ne, $in, etc.
            result = {}
            for op, val in value.items():
                if op in ("$in", "$nin") and isinstance(val, list):
                    result[op] = [self._to_object_id(v) for v in val]
                elif op.startswith("$"):
                    result[op] = self._to_object_id(val)
                else:
                    result[op] = val
            return result
        
        return value
    
    def normalizeId(self, id_value: Any) -> Any:
        """Normalize ID to MongoDB ObjectId."""
        return self._to_object_id(id_value)
    
    def denormalizeId(self, id_value: Any) -> str:
        """Convert MongoDB ObjectId to string."""
        return str(id_value) if id_value else None
