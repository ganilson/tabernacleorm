"""
PostgreSQL engine implementation for TabernacleORM.
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, date
from uuid import UUID
import json

from .base import BaseEngine


class PostgreSQLEngine(BaseEngine):
    """
    PostgreSQL database engine.
    
    Uses asyncpg for async connections.
    """
    
    def __init__(self, config):
        super().__init__(config)
        self._pool = None
        self._transaction = None
    
    async def connect(self) -> None:
        """Establish connection to PostgreSQL database."""
        try:
            import asyncpg
        except ImportError:
            raise ImportError(
                "asyncpg is required for PostgreSQL. "
                "Install with: pip install tabernacleorm[postgresql]"
            )
        
        # Build connection string
        url = self.config.url
        if not url.startswith("postgresql://") and not url.startswith("postgres://"):
            user = self.config.user or "postgres"
            password = self.config.password or ""
            host, rest = url.split("/") if "/" in url else (url, self.config.database or "postgres")
            if ":" in host:
                host, port = host.split(":")
            else:
                port = "5432"
            url = f"postgresql://{user}:{password}@{host}:{port}/{rest}"
        
        self._pool = await asyncpg.create_pool(
            url,
            min_size=1,
            max_size=self.config.pool_size,
            command_timeout=self.config.timeout,
        )
        self._connected = True
        
        if self.config.echo:
            print(f"[PostgreSQL] Connected to pool with {self.config.pool_size} connections")
    
    async def disconnect(self) -> None:
        """Close the PostgreSQL connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._connected = False
    
    async def _execute(
        self,
        sql: str,
        params: Optional[Tuple] = None,
        fetch: bool = True
    ) -> List[Dict[str, Any]]:
        """Execute SQL query."""
        if self.config.echo:
            print(f"[PostgreSQL] {sql}")
            if params:
                print(f"[PostgreSQL] Params: {params}")
        
        # Convert ? placeholders to $1, $2, etc. for asyncpg
        if params:
            for i in range(len(params), 0, -1):
                sql = sql.replace("?", f"${i}", 1)
            sql = sql.replace("?", f"${len(params) + 1}")
            # Fix: proper replacement
            sql_new = ""
            param_idx = 1
            for char in sql:
                if char == "?":
                    sql_new += f"${param_idx}"
                    param_idx += 1
                else:
                    sql_new += char
            sql = sql_new if "?" not in sql else sql
        
        async with self._pool.acquire() as conn:
            if self._transaction:
                conn = self._transaction
            
            if fetch:
                rows = await conn.fetch(sql, *params)
                return [dict(row) for row in rows]
            else:
                await conn.execute(sql, *params)
                return []
    
    async def insertOne(
        self,
        collection: str,
        document: Dict[str, Any]
    ) -> Any:
        """Insert a single document."""
        fields = []
        placeholders = []
        values = []
        
        for i, (key, value) in enumerate(document.items()):
            if key == "id" and value is None:
                continue
            fields.append(key)
            placeholders.append(f"${param_idx}")
            values.append(self._serialize_value(value))
            param_idx += 1
        
        sql = f"INSERT INTO {collection} ({', '.join(fields)}) VALUES ({', '.join(placeholders)}) RETURNING id"
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, *values)
            return row["id"] if row else None
    
    async def insert_many(
        self,
        collection: str,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> List[Any]:
        """Insert multiple documents using COPY or batch inserts."""
        ids = []
        
        # Use executemany for batched inserts
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            for doc in batch:
                doc_id = await self.insert_one(collection, doc)
                ids.append(doc_id)
        
        return ids
    
    async def find_one(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Find a single document."""
        results = await self.find_many(
            collection, query, projection=projection, limit=1
        )
        return results[0] if results else None
    
    async def find_many(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[List[str]] = None,
        sort: Optional[List[Tuple[str, int]]] = None,
        skip: int = 0,
        limit: int = 0
    ) -> List[Dict[str, Any]]:
        """Find multiple documents."""
        fields = ", ".join(projection) if projection else "*"
        sql = f"SELECT {fields} FROM {collection}"
        params = []
        param_idx = 1
        
        if query:
            conditions, cond_params, param_idx = self._build_where_clause(query, param_idx)
            if conditions:
                sql += f" WHERE {conditions}"
                params.extend(cond_params)
        
        if sort:
            order_parts = [f"{f} {'ASC' if d == 1 else 'DESC'}" for f, d in sort]
            sql += f" ORDER BY {', '.join(order_parts)}"
        
        if limit > 0:
            sql += f" LIMIT {limit}"
        if skip > 0:
            sql += f" OFFSET {skip}"
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [self._deserialize_row(dict(row)) for row in rows]
    
    async def update_one(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> int:
        """Update a single document."""
        update_data = update.get("$set", update)
        
        doc = await self.find_one(collection, query, projection=["id"])
        
        if not doc and upsert:
            await self.insert_one(collection, {**query, **update_data})
            return 1
        elif not doc:
            return 0
        
        set_parts = []
        values = []
        param_idx = 1
        
        for key, value in update_data.items():
            set_parts.append(f"{key} = ${param_idx}")
            values.append(self._serialize_value(value))
            param_idx += 1
        
        values.append(doc["id"])
        sql = f"UPDATE {collection} SET {', '.join(set_parts)} WHERE id = ${param_idx}"
        
        async with self._pool.acquire() as conn:
            result = await conn.execute(sql, *values)
            return int(result.split()[-1]) if result else 0
    
    async def update_many(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """Update multiple documents."""
        update_data = update.get("$set", update)
        
        set_parts = []
        values = []
        param_idx = 1
        
        for key, value in update_data.items():
            set_parts.append(f"{key} = ${param_idx}")
            values.append(self._serialize_value(value))
            param_idx += 1
        
        sql = f"UPDATE {collection} SET {', '.join(set_parts)}"
        
        if query:
            conditions, cond_params, _ = self._build_where_clause(query, param_idx)
            if conditions:
                sql += f" WHERE {conditions}"
                values.extend(cond_params)
        
        async with self._pool.acquire() as conn:
            result = await conn.execute(sql, *values)
            return int(result.split()[-1]) if result else 0
    
    async def delete_one(self, collection: str, query: Dict[str, Any]) -> int:
        """Delete a single document."""
        doc = await self.find_one(collection, query, projection=["id"])
        if not doc:
            return 0
        
        sql = f"DELETE FROM {collection} WHERE id = $1"
        async with self._pool.acquire() as conn:
            await conn.execute(sql, doc["id"])
            return 1
    
    async def delete_many(self, collection: str, query: Dict[str, Any]) -> int:
        """Delete multiple documents."""
        sql = f"DELETE FROM {collection}"
        params = []
        
        if query:
            conditions, cond_params, _ = self._build_where_clause(query, 1)
            if conditions:
                sql += f" WHERE {conditions}"
                params.extend(cond_params)
        
        async with self._pool.acquire() as conn:
            result = await conn.execute(sql, *params)
            return int(result.split()[-1]) if result else 0
    
    async def count(self, collection: str, query: Dict[str, Any]) -> int:
        """Count documents matching query."""
        sql = f"SELECT COUNT(*) as count FROM {collection}"
        params = []
        
        if query:
            conditions, cond_params, _ = self._build_where_clause(query, 1)
            if conditions:
                sql += f" WHERE {conditions}"
                params.extend(cond_params)
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, *params)
            return row["count"] if row else 0
    
    async def aggregate(
        self,
        collection: str,
        pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute aggregation pipeline (translated to SQL)."""
        # Similar to SQLite implementation
        sql_parts = [f"SELECT * FROM {collection}"]
        params = []
        group_by = None
        param_idx = 1
        
        for stage in pipeline:
            if "$match" in stage:
                conditions, cond_params, param_idx = self._build_where_clause(
                    stage["$match"], param_idx
                )
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
                            select_parts.append(f"AVG({agg['$avg'].replace('$', '')}) as {key}")
                        elif "$min" in agg:
                            select_parts.append(f"MIN({agg['$min'].replace('$', '')}) as {key}")
                        elif "$max" in agg:
                            select_parts.append(f"MAX({agg['$max'].replace('$', '')}) as {key}")
                
                sql_parts[0] = f"SELECT {', '.join(select_parts)} FROM {collection}"
            
            elif "$sort" in stage:
                order_parts = [f"{f} {'ASC' if d == 1 else 'DESC'}" for f, d in stage["$sort"].items()]
                sql_parts.append(f"ORDER BY {', '.join(order_parts)}")
            
            elif "$limit" in stage:
                sql_parts.append(f"LIMIT {stage['$limit']}")
            
            elif "$skip" in stage:
                sql_parts.append(f"OFFSET {stage['$skip']}")
        
        if group_by:
            for i, part in enumerate(sql_parts):
                if part.startswith("ORDER BY"):
                    sql_parts.insert(i, f"GROUP BY {group_by}")
                    break
            else:
                sql_parts.append(f"GROUP BY {group_by}")
        
        sql = " ".join(sql_parts)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [dict(row) for row in rows]
    
    async def create_collection(
        self,
        name: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a table."""
        if schema:
            columns = [self._field_to_column(f, s) for f, s in schema.items()]
            sql = f"CREATE TABLE IF NOT EXISTS {name} ({', '.join(columns)})"
        else:
            sql = f"CREATE TABLE IF NOT EXISTS {name} (id SERIAL PRIMARY KEY)"
        
        async with self._pool.acquire() as conn:
            await conn.execute(sql)
    
    async def drop_collection(self, name: str) -> None:
        """Drop a table."""
        async with self._pool.acquire() as conn:
            await conn.execute(f"DROP TABLE IF EXISTS {name} CASCADE")
    
    async def collection_exists(self, name: str) -> bool:
        """Check if table exists."""
        sql = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = $1
            )
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, name)
            return row[0] if row else False
    
    async def create_index(
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
        sql = f"CREATE {unique_str}INDEX IF NOT EXISTS {name} ON {collection} ({', '.join(fields)})"
        
        async with self._pool.acquire() as conn:
            await conn.execute(sql)
        return name
    
    async def drop_index(self, collection: str, name: str) -> None:
        """Drop an index."""
        async with self._pool.acquire() as conn:
            await conn.execute(f"DROP INDEX IF EXISTS {name}")
    
    async def _begin_transaction(self) -> None:
        """Begin a transaction."""
        self._transaction = await self._pool.acquire()
        await self._transaction.execute("BEGIN")
    
    async def _commit_transaction(self) -> None:
        """Commit the current transaction."""
        if self._transaction:
            await self._transaction.execute("COMMIT")
            await self._pool.release(self._transaction)
            self._transaction = None
    
    async def _rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        if self._transaction:
            await self._transaction.execute("ROLLBACK")
            await self._pool.release(self._transaction)
            self._transaction = None
    
    async def execute_raw(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """Execute a raw SQL query."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *(params or []))
            return [dict(row) for row in rows]
    
    async def explain(
        self,
        collection: str,
        query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Explain query execution plan."""
        sql = f"EXPLAIN ANALYZE SELECT * FROM {collection}"
        params = []
        
        if query:
            conditions, cond_params, _ = self._build_where_clause(query, 1)
            if conditions:
                sql += f" WHERE {conditions}"
                params.extend(cond_params)
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return {"plan": [row[0] for row in rows]}
    
    def _build_where_clause(
        self,
        query: Dict[str, Any],
        start_idx: int = 1
    ) -> Tuple[str, List[Any], int]:
        """Build WHERE clause from query dict."""
        conditions = []
        params = []
        param_idx = start_idx
        
        for key, value in query.items():
            if isinstance(value, dict):
                for op, val in value.items():
                    if op == "$gt":
                        conditions.append(f"{key} > ${param_idx}")
                    elif op == "$gte":
                        conditions.append(f"{key} >= ${param_idx}")
                    elif op == "$lt":
                        conditions.append(f"{key} < ${param_idx}")
                    elif op == "$lte":
                        conditions.append(f"{key} <= ${param_idx}")
                    elif op == "$ne":
                        conditions.append(f"{key} != ${param_idx}")
                    elif op == "$in":
                        placeholders = ", ".join(f"${param_idx + i}" for i in range(len(val)))
                        conditions.append(f"{key} IN ({placeholders})")
                        params.extend(val)
                        param_idx += len(val) - 1
                    elif op == "$like":
                        conditions.append(f"{key} LIKE ${param_idx}")
                        val = f"%{val}%"
                    else:
                        continue
                    
                    if op != "$in":
                        params.append(val)
                        param_idx += 1
            elif value is None:
                conditions.append(f"{key} IS NULL")
            else:
                conditions.append(f"{key} = ${param_idx}")
                params.append(value)
                param_idx += 1
        
        return " AND ".join(conditions), params, param_idx
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize value for storage."""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return value
    
    def _deserialize_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize row from storage."""
        return row
    
    def _field_to_column(self, name: str, spec: Dict[str, Any]) -> str:
        """Convert field spec to column definition."""
        type_map = {
            "string": "TEXT",
            "integer": "INTEGER",
            "float": "DOUBLE PRECISION",
            "boolean": "BOOLEAN",
            "datetime": "TIMESTAMP",
            "date": "DATE",
            "uuid": "UUID",
            "json": "JSONB",
            "array": "JSONB",
        }
        
        sql_type = type_map.get(spec.get("type", "string"), "TEXT")
        parts = [name, sql_type]
        
        if spec.get("primary_key"):
            if spec.get("auto_increment"):
                parts[1] = "SERIAL"
            parts.append("PRIMARY KEY")
        
        if spec.get("required") and not spec.get("primary_key"):
            parts.append("NOT NULL")
        
        if spec.get("unique") and not spec.get("primary_key"):
            parts.append("UNIQUE")
        
        return " ".join(parts)
