"""
QuerySet for TabernacleORM - Async, Engine-agnostic query builder.
"""

from typing import Any, Generic, Iterator, List, Optional, Tuple, Type, TypeVar, Dict, Union, Coroutine
import asyncio

T = TypeVar("T")

class QuerySet(Generic[T]):
    """Async lazy query builder."""
    
    def __init__(self, model: Type[T]):
        self.model = model
        # Filters stored as (field, operator, value)
        # operator is "$eq", "$gt", "$in", etc.
        self._filters: List[Tuple[str, str, Any]] = []
        self._order_by: List[Tuple[str, int]] = [] # field, direction (1 or -1)
        self._limit: int = 0
        self._includes: List[str] = [] # Eager loading
        self._lean: bool = False # Return plain dicts
    
    def _clone(self) -> "QuerySet[T]":
        """Create a copy of this QuerySet."""
        clone = QuerySet(self.model)
        clone._filters = self._filters.copy()
        clone._order_by = self._order_by.copy()
        clone._limit = self._limit
        clone._offset = self._offset
        clone._projection = self._projection
        clone._session = self._session
        clone._includes = self._includes.copy()
        clone._lean = self._lean
        return clone

    def lean(self) -> "QuerySet[T]":
        """Optimize query by returning plain dictionaries instead of Model instances."""
        clone = self._clone()
        clone._lean = True
        return clone

    async def all(self) -> Union[List[T], List[Dict[str, Any]]]:
        """Execute query and return list of Pydantic models with eager loading."""
        engine = self.model.get_engine()
        query = await self._build_engine_query()
        
        # Determine connection source
        conn_arg = {"_connection": self._session.connection} if self._session else {}

        raw_data = await engine.findMany(
            collection=self.model.get_table_name(),
            query=query,
            projection=self._projection,
            sort=self._order_by,
            skip=self._offset,
            limit=self._limit,
            **conn_arg
        )
        
        if self._lean:
             return raw_data

        # Convert dictionaries to Pydantic models
        models = [self.model(**row) for row in raw_data]
        
        # Handle Eager Loading
        if self._includes and models:
            for relation in self._includes:
                # Naive implementation: iterate and fetch (N+1 in python app layer, better than nothing)
                for m in models:
                    try:
                        related_data = await m.fetch_related(relation)
                        setattr(m, relation, related_data)
                    except Exception:
                        pass # Relation might fail or not be defined
                        
        return models

    def with_session(self, session) -> "QuerySet[T]":
        """Bind query to a specific session."""
        clone = self._clone()
        clone._session = session
        return clone

    def filter(self, **kwargs) -> "QuerySet[T]":
        """Add filter conditions (Django-style)."""
        clone = self._clone()
        for key, value in kwargs.items():
            if "__" in key:
                parts = key.split("__")
                field = parts[0]
                op_suffix = parts[1]
                
                op_map = {
                    "gt": "$gt", "gte": "$gte",
                    "lt": "$lt", "lte": "$lte",
                    "ne": "$ne", "in": "$in",
                    "nin": "$nin",
                    "like": "$like", "contains": "$like",
                    "startswith": "$like", "endswith": "$like",
                }
                
                op = op_map.get(op_suffix, "$eq")
                
                # Adjust values for like
                if op_suffix == "contains": value = f"%{value}%"
                if op_suffix == "startswith": value = f"{value}%"
                if op_suffix == "endswith": value = f"%{value}"
            else:
                field = key
                op = "$eq"
            
            clone._filters.append((field, op, value))
        return clone

    def filter_expr(self, *args) -> "QuerySet[T]":
        """Add filter conditions from expressions."""
        clone = self._clone()
        for expr in args:
            # Expr is expected to be a tuple (op, field, value) from ColumnExpression
            if isinstance(expr, tuple) and len(expr) == 3:
                op, field, value = expr
                clone._filters.append((field, op, value))
        return clone
    
    def exclude(self, **kwargs) -> "QuerySet[T]":
        """Exclude records (invert logic)."""
        # Complex inversion logic is hard with simple query dicts
        # For now, implement simple 'ne'
        clone = self._clone()
        for key, value in kwargs.items():
            clone._filters.append((key, "$ne", value))
        return clone
    
    def order_by(self, *fields: str) -> "QuerySet[T]":
        """Order results."""
        clone = self._clone()
        for field in fields:
            direction = 1
            if field.startswith("-"):
                field = field[1:]
                direction = -1
            clone._order_by.append((field, direction))
        return clone
    
    def limit(self, count: int) -> "QuerySet[T]":
        clone = self._clone()
        clone._limit = count
        return clone
    
    def offset(self, count: int) -> "QuerySet[T]":
        clone = self._clone()
        clone._offset = count
        return clone
    
    def include(self, *relations: str) -> "QuerySet[T]":
        """Eager load relationships."""
        clone = self._clone()
        if clone._includes is None:
            clone._includes = []
        clone._includes.extend(relations)
        return clone

    async def _build_engine_query(self) -> Dict[str, Any]:
        """Convert filters to Engine dictionary format."""
        query = {}
        for field, op, value in self._filters:
            if op == "$eq":
                query[field] = value
            else:
                if field not in query:
                    query[field] = {}
                elif not isinstance(query[field], dict):
                    # Conflict: was scalar, now dict
                    query[field] = {"$eq": query[field]}
                
                query[field][op] = value
        return query



    async def first(self) -> Optional[T]:
        """Get first result."""
        res = await self.limit(1).all()
        return res[0] if res else None

    async def get(self, **kwargs) -> Optional[T]:
        """Get single result."""
        return await self.filter(**kwargs).first()

    async def count(self) -> int:
        """Count records."""
        engine = self.model.get_engine()
        query = await self._build_engine_query()
        conn_arg = {"_connection": self._session.connection} if self._session else {}
        
        return await engine.count(
            collection=self.model.get_table_name(),
            query=query,
            **conn_arg
        )

    async def delete(self) -> int:
        """Delete matching records."""
        engine = self.model.get_engine()
        query = await self._build_engine_query()
        conn_arg = {"_connection": self._session.connection} if self._session else {}
        
        return await engine.deleteMany(
            collection=self.model.get_table_name(),
            query=query,
            **conn_arg
        )

    async def update(self, **kwargs) -> int:
        """Update matching records."""
        engine = self.model.get_engine()
        query = await self._build_engine_query()
        conn_arg = {"_connection": self._session.connection} if self._session else {}
        
        cleaned_update = {}
        if "$set" in kwargs:
             cleaned_update = kwargs # assume raw update
        else:
             cleaned_update = {"$set": kwargs}

        return await engine.updateMany(
            collection=self.model.get_table_name(),
            query=query,
            update=cleaned_update,
            **conn_arg
        )

    def __await__(self):
        """Allow 'await QuerySet' to execute .all() implicitly."""
        return self.all().__await__()
