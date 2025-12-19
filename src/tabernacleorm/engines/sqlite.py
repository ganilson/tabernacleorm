"""
SQLite engine implementation for TabernacleORM.
"""

import sqlite3
import json
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, date
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor

from .base import BaseEngine


class SQLiteEngine(BaseEngine):
    """
    SQLite database engine.
    
    Uses sqlite3 with async wrapper via ThreadPoolExecutor.
    """
    
    def __init__(self, config):
        super().__init__(config)
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._in_transaction = False
    
    async def connect(self) -> None:
        """Establish connection to SQLite database."""
        url = self.config.url or ":memory:"
        
        # Remove sqlite:/// prefix if present
        if url.startswith("sqlite:///"):
            url = url[10:]
        elif url.startswith("sqlite://"):
            url = url[9:]
        
        def _connect():
            conn = sqlite3.connect(
                url,
                check_same_thread=self.config.check_same_thread,
                timeout=self.config.timeout
            )
            conn.row_factory = sqlite3.Row
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            # Enable WAL mode for better performance
            conn.execute("PRAGMA journal_mode = WAL")
            return conn
        
        loop = asyncio.get_event_loop()
        self._connection = await loop.run_in_executor(self._executor, _connect)
        self._connected = True
        
        if self.config.echo:
            print(f"[SQLite] Connected to: {url}")
    
    async def disconnect(self) -> None:
        """Close the SQLite connection."""
        if self._connection:
            def _close():
                self._connection.close()
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self._executor, _close)
            self._connection = None
            self._connected = False
            self._executor.shutdown(wait=False)
    
    async def _execute(
        self,
        sql: str,
        params: Optional[Tuple] = None,
        fetch: bool = True
    ) -> List[Dict[str, Any]]:
        """Execute SQL query."""
        if self.config.echo:
            print(f"[SQLite] {sql}")
            if params:
                print(f"[SQLite] Params: {params}")
        
        def _run():
            cursor = self._connection.cursor()
            try:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                if fetch:
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
                else:
                    if not self._in_transaction:
                        self._connection.commit()
                    return []
            except sqlite3.OperationalError as e:
                msg = str(e)
                if "no such table" in msg:
                    table = msg.split(":")[-1].strip() if ":" in msg else "unknown"
                    raise RuntimeError(
                        f"Table not found (Error: {e}). "
                        f"Did you forget to run 'tabernacle makemigrations' and 'tabernacle migrate'?"
                    )
                raise e
            finally:
                cursor.close()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, _run)
    
    async def insertOne(
        self,
        collection: str,
        document: Dict[str, Any]
    ) -> Any:
        """Insert a single document."""
        fields = []
        placeholders = []
        values = []
        
        for key, value in document.items():
            if key == "id" and value is None:
                continue
            fields.append(key)
            placeholders.append("?")
            values.append(self._serializeValue(value))
        
        sql = f"INSERT INTO {collection} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
        await self._execute(sql, tuple(values), fetch=False)
        
        # Get last inserted ID
        result = await self._execute("SELECT last_insert_rowid() as id")
        return result[0]["id"] if result else None
    
    async def insertMany(
        self,
        collection: str,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> List[Any]:
        """Insert multiple documents in batches."""
        ids = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            for doc in batch:
                doc_id = await self.insertOne(collection, doc)
                ids.append(doc_id)
        
        return ids
    
    async def findOne(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Find a single document."""
        results = await self.findMany(
            collection, query, projection=projection, limit=1
        )
        return results[0] if results else None
    
    async def findMany(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[List[str]] = None,
        sort: Optional[List[Tuple[str, int]]] = None,
        skip: int = 0,
        limit: int = 0
    ) -> List[Dict[str, Any]]:
        """Find multiple documents."""
        # Build SELECT clause
        if projection:
            fields = ", ".join(projection)
        else:
            fields = "*"
        
        sql = f"SELECT {fields} FROM {collection}"
        params = []
        
        # Build WHERE clause
        if query:
            conditions, cond_params = self._buildWhereClause(query)
            if conditions:
                sql += f" WHERE {conditions}"
                params.extend(cond_params)
        
        # Build ORDER BY clause
        if sort:
            order_parts = []
            for field, direction in sort:
                order_parts.append(f"{field} {'ASC' if direction == 1 else 'DESC'}")
            sql += f" ORDER BY {', '.join(order_parts)}"
        
        # Build LIMIT/OFFSET
        if limit > 0:
            sql += f" LIMIT {limit}"
        if skip > 0:
            sql += f" OFFSET {skip}"
        
        results = await self._execute(sql, tuple(params) if params else None)
        return [self._deserializeRow(row) for row in results]
    
    async def updateOne(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> int:
        """Update a single document."""
        # Handle $set operator
        if "$set" in update:
            update_data = update["$set"]
        else:
            update_data = update
        
        # Find the document first to get its ID
        doc = await self.findOne(collection, query, projection=["id"])
        
        if not doc and upsert:
            # Insert new document
            await self.insertOne(collection, {**query, **update_data})
            return 1
        elif not doc:
            return 0
        
        # Build UPDATE statement
        set_parts = []
        values = []
        for key, value in update_data.items():
            set_parts.append(f"{key} = ?")
            values.append(self._serializeValue(value))
        
        values.append(doc["id"])
        sql = f"UPDATE {collection} SET {', '.join(set_parts)} WHERE id = ?"
        
        await self._execute(sql, tuple(values), fetch=False)
        return 1
    
    async def updateMany(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """Update multiple documents."""
        # Handle $set operator
        if "$set" in update:
            update_data = update["$set"]
        else:
            update_data = update
        
        # Build SET clause
        set_parts = []
        values = []
        for key, value in update_data.items():
            set_parts.append(f"{key} = ?")
            values.append(self._serializeValue(value))
        
        sql = f"UPDATE {collection} SET {', '.join(set_parts)}"
        
        # Build WHERE clause
        if query:
            conditions, cond_params = self._buildWhereClause(query)
            if conditions:
                sql += f" WHERE {conditions}"
                values.extend(cond_params)
        
        await self._execute(sql, tuple(values), fetch=False)
        
        # Get affected rows count
        result = await self._execute("SELECT changes() as count")
        return result[0]["count"] if result else 0
    
    async def deleteOne(
        self,
        collection: str,
        query: Dict[str, Any]
    ) -> int:
        """Delete a single document."""
        doc = await self.findOne(collection, query, projection=["id"])
        if not doc:
            return 0
        
        sql = f"DELETE FROM {collection} WHERE id = ?"
        await self._execute(sql, (doc["id"],), fetch=False)
        return 1
    
    async def deleteMany(
        self,
        collection: str,
        query: Dict[str, Any]
    ) -> int:
        """Delete multiple documents."""
        sql = f"DELETE FROM {collection}"
        params = []
        
        if query:
            conditions, cond_params = self._buildWhereClause(query)
            if conditions:
                sql += f" WHERE {conditions}"
                params.extend(cond_params)
        
        await self._execute(sql, tuple(params) if params else None, fetch=False)
        
        result = await self._execute("SELECT changes() as count")
        return result[0]["count"] if result else 0
    
    async def count(
        self,
        collection: str,
        query: Dict[str, Any]
    ) -> int:
        """Count documents matching query."""
        sql = f"SELECT COUNT(*) as count FROM {collection}"
        params = []
        
        if query:
            conditions, cond_params = self._buildWhereClause(query)
            if conditions:
                sql += f" WHERE {conditions}"
                params.extend(cond_params)
        
        result = await self._execute(sql, tuple(params) if params else None)
        return result[0]["count"] if result else 0
    
    async def aggregate(
        self,
        collection: str,
        pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute aggregation pipeline (translated to SQL)."""
        # Basic aggregation translation
        # Full MongoDB aggregation pipeline would require complex translation
        sql_parts = [f"SELECT * FROM {collection}"]
        params = []
        group_by = None
        
        for stage in pipeline:
            if "$match" in stage:
                conditions, cond_params = self._buildWhereClause(stage["$match"])
                if conditions:
                    sql_parts.append(f"WHERE {conditions}")
                    params.extend(cond_params)
            
            elif "$group" in stage:
                group_spec = stage["$group"]
                group_field = group_spec.get("_id", "").replace("$", "")
                
                select_parts = []
                if group_field:
                    select_parts.append(f"{group_field} as _id")
                    group_by = group_field
                
                for key, agg in group_spec.items():
                    if key == "_id":
                        continue
                    if isinstance(agg, dict):
                        if "$sum" in agg:
                            field = agg["$sum"]
                            if field == 1:
                                select_parts.append(f"COUNT(*) as {key}")
                            else:
                                select_parts.append(f"SUM({field.replace('$', '')}) as {key}")
                        elif "$avg" in agg:
                            field = agg["$avg"].replace("$", "")
                            select_parts.append(f"AVG({field}) as {key}")
                        elif "$min" in agg:
                            field = agg["$min"].replace("$", "")
                            select_parts.append(f"MIN({field}) as {key}")
                        elif "$max" in agg:
                            field = agg["$max"].replace("$", "")
                            select_parts.append(f"MAX({field}) as {key}")
                
                sql_parts[0] = f"SELECT {', '.join(select_parts)} FROM {collection}"
            
            elif "$sort" in stage:
                order_parts = []
                for field, direction in stage["$sort"].items():
                    order_parts.append(f"{field} {'ASC' if direction == 1 else 'DESC'}")
                sql_parts.append(f"ORDER BY {', '.join(order_parts)}")
            
            elif "$limit" in stage:
                sql_parts.append(f"LIMIT {stage['$limit']}")
            
            elif "$skip" in stage:
                sql_parts.append(f"OFFSET {stage['$skip']}")
        
        if group_by:
            # Insert GROUP BY before ORDER BY
            for i, part in enumerate(sql_parts):
                if part.startswith("ORDER BY"):
                    sql_parts.insert(i, f"GROUP BY {group_by}")
                    break
            else:
                sql_parts.append(f"GROUP BY {group_by}")
        
        sql = " ".join(sql_parts)
        return await self._execute(sql, tuple(params) if params else None)
    
    async def createCollection(
        self,
        name: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a table."""
        if schema:
            columns = []
            for field_name, field_spec in schema.items():
                col_def = self._fieldToColumn(field_name, field_spec)
                columns.append(col_def)
            
            sql = f"CREATE TABLE IF NOT EXISTS {name} ({', '.join(columns)})"
        else:
            sql = f"CREATE TABLE IF NOT EXISTS {name} (id INTEGER PRIMARY KEY AUTOINCREMENT)"
        
        await self._execute(sql, fetch=False)
    
    async def dropCollection(self, name: str) -> None:
        """Drop a table."""
        sql = f"DROP TABLE IF EXISTS {name}"
        await self._execute(sql, fetch=False)
    
    async def collectionExists(self, name: str) -> bool:
        """Check if table exists."""
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
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
        fields_str = ", ".join(fields)
        sql = f"CREATE {unique_str}INDEX IF NOT EXISTS {name} ON {collection} ({fields_str})"
        
        await self._execute(sql, fetch=False)
        return name
    
    async def dropIndex(self, collection: str, name: str) -> None:
        """Drop an index."""
        sql = f"DROP INDEX IF EXISTS {name}"
        await self._execute(sql, fetch=False)
    
    async def _beginTransaction(self) -> None:
        """Begin a transaction."""
        self._in_transaction = True
        await self._execute("BEGIN TRANSACTION", fetch=False)
    
    async def _commitTransaction(self) -> None:
        """Commit the current transaction."""
        await self._execute("COMMIT", fetch=False)
        self._in_transaction = False
    
    async def _rollbackTransaction(self) -> None:
        """Rollback the current transaction."""
        await self._execute("ROLLBACK", fetch=False)
        self._in_transaction = False
    
    async def executeRaw(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """Execute a raw SQL query."""
        return await self._execute(query, params)
    
    async def explain(
        self,
        collection: str,
        query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Explain query execution plan."""
        sql = f"EXPLAIN QUERY PLAN SELECT * FROM {collection}"
        params = []
        
        if query:
            conditions, cond_params = self._buildWhereClause(query)
            if conditions:
                sql += f" WHERE {conditions}"
                params.extend(cond_params)
        
        result = await self._execute(sql, tuple(params) if params else None)
        return {"plan": result}
    
    def _buildWhereClause(
        self,
        query: Dict[str, Any]
    ) -> Tuple[str, List[Any]]:
        """Build WHERE clause from query dict."""
        conditions = []
        params = []
        
        for key, value in query.items():
            if isinstance(value, dict):
                # Handle operators
                for op, val in value.items():
                    if op == "$gt":
                        conditions.append(f"{key} > ?")
                        params.append(val)
                    elif op == "$gte":
                        conditions.append(f"{key} >= ?")
                        params.append(val)
                    elif op == "$lt":
                        conditions.append(f"{key} < ?")
                        params.append(val)
                    elif op == "$lte":
                        conditions.append(f"{key} <= ?")
                        params.append(val)
                    elif op == "$ne":
                        conditions.append(f"{key} != ?")
                        params.append(val)
                    elif op == "$in":
                        placeholders = ", ".join("?" * len(val))
                        conditions.append(f"{key} IN ({placeholders})")
                        params.extend(val)
                    elif op == "$nin":
                        placeholders = ", ".join("?" * len(val))
                        conditions.append(f"{key} NOT IN ({placeholders})")
                        params.extend(val)
                    elif op == "$like" or op == "$contains":
                        conditions.append(f"{key} LIKE ?")
                        params.append(f"%{val}%")
                    elif op == "$regex":
                        conditions.append(f"{key} REGEXP ?")
                        params.append(val)
            elif value is None:
                conditions.append(f"{key} IS NULL")
            else:
                conditions.append(f"{key} = ?")
                params.append(value)
        
        return " AND ".join(conditions), params
    
    def _serializeValue(self, value: Any) -> Any:
        """Serialize value for storage."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return value
    
    def _deserializeRow(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize row from storage."""
        result = {}
        for key, value in row.items():
            if isinstance(value, str):
                # Try to parse JSON
                if value.startswith("{") or value.startswith("["):
                    try:
                        result[key] = json.loads(value)
                        continue
                    except json.JSONDecodeError:
                        pass
            result[key] = value
        return result
    
    def _fieldToColumn(self, name: str, spec: Dict[str, Any]) -> str:
        """Convert field spec to column definition."""
        type_map = {
            "string": "TEXT",
            "integer": "INTEGER",
            "float": "REAL",
            "boolean": "INTEGER",
            "datetime": "TEXT",
            "date": "TEXT",
            "uuid": "TEXT",
            "json": "TEXT",
            "array": "TEXT",
        }
        
        field_type = spec.get("type", "string")
        sql_type = type_map.get(field_type, "TEXT")
        
        parts = [name, sql_type]
        
        if spec.get("primary_key"):
            parts.append("PRIMARY KEY")
            if spec.get("auto_increment"):
                parts.append("AUTOINCREMENT")
        
        if spec.get("required") and not spec.get("primary_key"):
            parts.append("NOT NULL")
        
        if spec.get("unique") and not spec.get("primary_key"):
            parts.append("UNIQUE")
        
        if "default" in spec:
            default = spec["default"]
            if isinstance(default, str):
                parts.append(f"DEFAULT '{default}'")
            elif isinstance(default, bool):
                parts.append(f"DEFAULT {1 if default else 0}")
            else:
                parts.append(f"DEFAULT {default}")
        
        return " ".join(parts)
