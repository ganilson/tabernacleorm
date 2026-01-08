"""
MySQL engine implementation for TabernacleORM.
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, date
from uuid import UUID
import json

from .base import BaseEngine
from typing import AsyncGenerator
from contextlib import asynccontextmanager


class MySQLEngine(BaseEngine):
    """
    MySQL database engine.
    
    Uses aiomysql for async connections.
    """
    
    def __init__(self, config):
        super().__init__(config)
        self._pool = None
    
    async def connect(self) -> None:
        """Establish connection to MySQL database."""
        try:
            import aiomysql
            from urllib.parse import urlparse, unquote
        except ImportError:
            raise ImportError(
                "aiomysql is required for MySQL. "
                "Install with: pip install tabernacleorm[mysql]"
            )
        
        # Parse connection info
        url = self.config.url or ""
        
        # Default values
        host = "localhost"
        port = 3306
        user = self.config.user or "root"
        password = self.config.password or ""
        db = self.config.database or "test"
        
        if "://" in url:
            parsed = urlparse(url)
            if parsed.scheme == "mysql":
                host = parsed.hostname or host
                port = parsed.port or port
                if parsed.username:
                    user = unquote(parsed.username)
                if parsed.password:
                    password = unquote(parsed.password)
                if parsed.path and parsed.path != "/":
                    db = parsed.path.lstrip("/")
        
        # Override with explicit config if provided and not default
        if self.config.user:
            user = self.config.user
        if self.config.password:
            password = self.config.password
        if self.config.host:
            host = self.config.host
        if self.config.port:
            port = int(self.config.port)
        if self.config.database:
            db = self.config.database

        self._pool = await aiomysql.create_pool(
            host=host,
            port=port,
            user=user,
            password=password,
            db=db,
            charset=self.config.charset or "utf8mb4",
            autocommit=True, # Auto-commit by default, use transactions explicitly
            minsize=1,
            maxsize=self.config.pool_size,
        )
        self._connected = True
        
        if self.config.echo:
            # Mask password in log
            print(f"[MySQL] Connected to mysql://{user}:***@{host}:{port}/{db}")
    
    async def disconnect(self) -> None:
        """Close the MySQL connection pool."""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None
            self._connected = False

    async def acquireConnection(self) -> Any:
        return await self._pool.acquire()

    async def releaseConnection(self, connection: Any) -> None:
        self._pool.release(connection)
    
    @asynccontextmanager
    async def _get_conn(self, _connection: Optional[Any] = None) -> AsyncGenerator[Any, None]:
        if _connection:
            yield _connection
        else:
            async with self._pool.acquire() as conn:
                yield conn
    
    async def _execute(
        self,
        sql: str,
        params: Optional[Tuple] = None,
        fetch: bool = True,
        _connection: Any = None
    ) -> List[Dict[str, Any]]:
        """Execute SQL query."""
        if self.config.echo:
            print(f"[MySQL] {sql}")
            if params:
                print(f"[MySQL] Params: {params}")
        
        async with self._get_conn(_connection) as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, params or ())
                
                if fetch:
                    rows = await cursor.fetchall()
                    return list(rows)
                else:
                    if not _connection:
                        await conn.commit()
                    return []
    

    async def insertOne(self, collection: str, document: Dict[str, Any], _connection: Any = None) -> Any:
        keys = []
        values = []
        placeholders = []
        for k, v in document.items():
            if k == "id" and v is None: continue
            keys.append(f"`{k}`")
            values.append(self._serialize_value(v))
            placeholders.append("%s")
            
        sql = f"INSERT INTO `{collection}` ({', '.join(keys)}) VALUES ({', '.join(placeholders)})"
        
        async with self._get_conn(_connection) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, tuple(values))
                if not _connection:
                    await conn.commit()
                return cursor.lastrowid
    
    async def insertMany(
        self,
        collection: str,
        documents: List[Dict[str, Any]],
        batch_size: int = 100,
        _connection: Any = None
    ) -> List[Any]:
        """Insert multiple documents using multi-row INSERT."""
        if not documents:
            return []
        
        ids = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            for doc in batch:
                doc_id = await self.insertOne(collection, doc, _connection=_connection)
                ids.append(doc_id)
        
        return ids
    
    async def findOne(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[List[str]] = None,
        _connection: Any = None
    ) -> Optional[Dict[str, Any]]:
        """Find a single document."""
        results = await self.findMany(collection, query, projection=projection, limit=1, _connection=_connection)
        return results[0] if results else None
    
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
        fields = ", ".join(f"`{f}`" for f in projection) if projection else "*"
        sql = f"SELECT {fields} FROM `{collection}`"
        params = []
        
        if query:
            conditions, cond_params = self._build_where_clause(query)
            if conditions:
                sql += f" WHERE {conditions}"
                params.extend(cond_params)
        
        if sort:
            order_parts = [f"`{f}` {'ASC' if d == 1 else 'DESC'}" for f, d in sort]
            sql += f" ORDER BY {', '.join(order_parts)}"
        
        if limit > 0:
            sql += f" LIMIT {limit}"
        if skip > 0:
            sql += f" OFFSET {skip}"
        
        try:
            import aiomysql
        except ImportError:
            raise ImportError("aiomysql required")
        
        async with self._get_conn(_connection) as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, tuple(params))
                rows = await cursor.fetchall()
                return [self._deserialize_row(dict(row)) for row in rows]
    
    async def updateOne(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
        _connection: Any = None
    ) -> int:
        """Update a single document."""
        update_data = update.get("$set", update)
        
        doc = await self.findOne(collection, query, projection=["id"], _connection=_connection)
        
        if not doc and upsert:
            await self.insertOne(collection, {**query, **update_data}, _connection=_connection)
            return 1
        elif not doc:
            return 0
        
        set_parts = []
        values = []
        
        for key, value in update_data.items():
            set_parts.append(f"`{key}` = %s")
            values.append(self._serialize_value(value))
        
        values.append(doc["id"])
        sql = f"UPDATE `{collection}` SET {', '.join(set_parts)} WHERE id = %s"
        
        async with self._get_conn(_connection) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, tuple(values))
                if not _connection:
                    await conn.commit()
                return cursor.rowcount
    
    async def updateMany(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        _connection: Any = None
    ) -> int:
        """Update multiple documents."""
        update_data = update.get("$set", update)
        
        set_parts = []
        values = []
        
        for key, value in update_data.items():
            set_parts.append(f"`{key}` = %s")
            values.append(self._serialize_value(value))
        
        sql = f"UPDATE `{collection}` SET {', '.join(set_parts)}"
        
        if query:
            conditions, cond_params = self._build_where_clause(query)
            if conditions:
                sql += f" WHERE {conditions}"
                values.extend(cond_params)
        
        async with self._get_conn(_connection) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, tuple(values))
                if not _connection:
                    await conn.commit()
                return cursor.rowcount
    
    async def deleteOne(self, collection: str, query: Dict[str, Any], _connection: Any = None) -> int:
        """Delete a single document."""
        doc = await self.findOne(collection, query, projection=["id"], _connection=_connection)
        if not doc:
            return 0
        
        sql = f"DELETE FROM `{collection}` WHERE id = %s"
        
        async with self._get_conn(_connection) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, (doc["id"],))
                if not _connection:
                    await conn.commit()
                return cursor.rowcount
    
    async def deleteMany(self, collection: str, query: Dict[str, Any], _connection: Any = None) -> int:
        """Delete multiple documents."""
        sql = f"DELETE FROM `{collection}`"
        params = []
        
        if query:
            conditions, cond_params = self._build_where_clause(query)
            if conditions:
                sql += f" WHERE {conditions}"
                params.extend(cond_params)
        
        async with self._get_conn(_connection) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, tuple(params))
                if not _connection:
                    await conn.commit()
                return cursor.rowcount
    
    async def count(self, collection: str, query: Dict[str, Any], _connection: Any = None) -> int:
        """Count documents matching query."""
        sql = f"SELECT COUNT(*) as count FROM `{collection}`"
        params = []
        
        if query:
            conditions, cond_params = self._build_where_clause(query)
            if conditions:
                sql += f" WHERE {conditions}"
                params.extend(cond_params)
        
        result = await self._execute(sql, tuple(params) if params else None, _connection=_connection)
        return result[0]["count"] if result else 0
    
    async def aggregate(
        self,
        collection: str,
        pipeline: List[Dict[str, Any]],
        _connection: Any = None
    ) -> List[Dict[str, Any]]:
        """Execute aggregation pipeline (translated to SQL)."""
        # Similar to SQLite/PostgreSQL implementation
        sql_parts = [f"SELECT * FROM `{collection}`"]
        params = []
        group_by = None
        
        for stage in pipeline:
            if "$match" in stage:
                conditions, cond_params = self._build_where_clause(stage["$match"])
                if conditions:
                    sql_parts.append(f"WHERE {conditions}")
                    params.extend(cond_params)
            
            elif "$group" in stage:
                group_spec = stage["$group"]
                group_field = group_spec.get("_id", "").replace("$", "")
                
                select_parts = []
                if group_field:
                    select_parts.append(f"`{group_field}` as _id")
                    group_by = group_field
                
                for key, agg in group_spec.items():
                    if key == "_id":
                        continue
                    if isinstance(agg, dict):
                        if "$sum" in agg:
                            field = agg["$sum"]
                            if field == 1:
                                select_parts.append(f"COUNT(*) as `{key}`")
                            else:
                                select_parts.append(f"SUM(`{field.replace('$', '')}`) as `{key}`")
                        elif "$avg" in agg:
                            select_parts.append(f"AVG(`{agg['$avg'].replace('$', '')}`) as `{key}`")
                
                sql_parts[0] = f"SELECT {', '.join(select_parts)} FROM `{collection}`"
            
            elif "$sort" in stage:
                order_parts = [f"`{f}` {'ASC' if d == 1 else 'DESC'}" for f, d in stage["$sort"].items()]
                sql_parts.append(f"ORDER BY {', '.join(order_parts)}")
            
            elif "$limit" in stage:
                sql_parts.append(f"LIMIT {stage['$limit']}")
        
        if group_by:
            for i, part in enumerate(sql_parts):
                if part.startswith("ORDER BY"):
                    sql_parts.insert(i, f"GROUP BY `{group_by}`")
                    break
            else:
                sql_parts.append(f"GROUP BY `{group_by}`")
        
        sql = " ".join(sql_parts)
        return await self._execute(sql, tuple(params) if params else None, _connection=_connection)
    
    async def createCollection(
        self,
        name: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a table."""
        if schema:
            columns = [self._field_to_column(f, s) for f, s in schema.items()]
            sql = f"CREATE TABLE IF NOT EXISTS `{name}` ({', '.join(columns)}) ENGINE=InnoDB DEFAULT CHARSET={self.config.charset}"
        else:
            sql = f"CREATE TABLE IF NOT EXISTS `{name}` (id INT AUTO_INCREMENT PRIMARY KEY) ENGINE=InnoDB"
        
        await self._execute(sql, fetch=False)
    
    async def dropCollection(self, name: str) -> None:
        """Drop a table."""
        await self._execute(f"DROP TABLE IF EXISTS `{name}`", fetch=False)
    
    async def collectionExists(self, name: str) -> bool:
        """Check if table exists."""
        sql = "SHOW TABLES LIKE %s"
        result = await self._execute(sql, (name,))
        return len(result) > 0
    
    async def createIndex(
        self,
        collection: str,
        fields: List[str],
        unique: bool = False,
        name: Optional[str] = None
    ) -> str:
        """Create an index."""
        if not name:
            name = f"idx_{collection}_{'_'.join(fields)}"
        
        unique_str = "UNIQUE " if unique else ""
        fields_str = ", ".join(f"`{f}`" for f in fields)
        sql = f"CREATE {unique_str}INDEX `{name}` ON `{collection}` ({fields_str})"
        
        try:
            await self._execute(sql, fetch=False)
        except Exception:
            pass  # Index may already exist
        
        return name
    
    async def dropIndex(self, collection: str, name: str) -> None:
        """Drop an index."""
        await self._execute(f"DROP INDEX `{name}` ON `{collection}`", fetch=False)
    
    async def beginTransaction(self, connection: Any) -> None:
        """Begin a transaction."""
        await connection.begin()
    
    async def commitTransaction(self, connection: Any) -> None:
        """Commit the current transaction."""
        await connection.commit()
    
    async def rollbackTransaction(self, connection: Any) -> None:
        """Rollback the current transaction."""
        await connection.rollback()
    
    async def executeRaw(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """Execute a raw SQL query."""
        return await self._execute(query, params)
    
    def _build_where_clause(self, query: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """Build WHERE clause from query dict (using shared translator)."""
        from .sql_translator import build_where_clause
        
        # MySQL uses %s for placeholders (aiomysql)
        conditions, params = build_where_clause(query, dialect="mysql")
        if not conditions:
            return "", []
            
        # Convert '?' to '%s'
        conditions = conditions.replace("?", "%s")
        
        return conditions, params
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize value for storage."""
        if value is None:
            return None
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        if isinstance(value, UUID):
            return str(value) if self.config.uuid_storage == "string" else value.bytes
        return value
    
    def _deserialize_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize row from storage."""
        return row
    
    def _field_to_column(self, name: str, spec: Dict[str, Any]) -> str:
        """Convert field spec to column definition."""
        type_map = {
            "string": "VARCHAR(255)",
            "text": "TEXT",
            "integer": "INT",
            "float": "DOUBLE",
            "boolean": "TINYINT(1)",
            "datetime": "DATETIME",
            "date": "DATE",
            "uuid": "CHAR(36)" if self.config.uuid_storage == "string" else "BINARY(16)",
            "json": "JSON",
            "array": "JSON",
        }
        
        sql_type = type_map.get(spec.get("type", "string"), "VARCHAR(255)")
        parts = [f"`{name}`", sql_type]
        
        if spec.get("primary_key"):
            if spec.get("auto_increment"):
                parts.append("AUTO_INCREMENT")
            parts.append("PRIMARY KEY")
        
        if spec.get("required") and not spec.get("primary_key"):
            parts.append("NOT NULL")
        
        if spec.get("unique") and not spec.get("primary_key"):
            parts.append("UNIQUE")
        
        return " ".join(parts)
