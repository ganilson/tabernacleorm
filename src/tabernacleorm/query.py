"""
QuerySet for TabernacleORM - Lazy query building and execution.
"""

from typing import Any, Generic, Iterator, List, Optional, Tuple, Type, TypeVar

T = TypeVar("T")


class QuerySet(Generic[T]):
    """Lazy query builder for database queries."""
    
    def __init__(self, model: Type[T]):
        self.model = model
        self._filters: List[Tuple[str, str, Any]] = []
        self._order_by: List[Tuple[str, str]] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._cache: Optional[List[T]] = None
    
    def _clone(self) -> "QuerySet[T]":
        """Create a copy of this QuerySet."""
        clone = QuerySet(self.model)
        clone._filters = self._filters.copy()
        clone._order_by = self._order_by.copy()
        clone._limit = self._limit
        clone._offset = self._offset
        return clone
    
    def filter(self, **kwargs) -> "QuerySet[T]":
        """Add filter conditions."""
        clone = self._clone()
        for key, value in kwargs.items():
            # Support for operators like field__gt, field__lt, etc.
            if "__" in key:
                parts = key.split("__")
                field = parts[0]
                operator = parts[1]
                
                op_map = {
                    "gt": ">",
                    "gte": ">=",
                    "lt": "<",
                    "lte": "<=",
                    "ne": "!=",
                    "in": "IN",
                    "like": "LIKE",
                    "ilike": "LIKE",  # SQLite is case-insensitive by default
                    "contains": "LIKE",
                    "startswith": "LIKE",
                    "endswith": "LIKE",
                    "isnull": "IS NULL" if value else "IS NOT NULL",
                }
                
                if operator in op_map:
                    sql_op = op_map[operator]
                    
                    # Transform value for LIKE operators
                    if operator == "contains":
                        value = f"%{value}%"
                    elif operator == "startswith":
                        value = f"{value}%"
                    elif operator == "endswith":
                        value = f"%{value}"
                    elif operator == "isnull":
                        value = None
                    
                    clone._filters.append((field, sql_op, value))
                else:
                    raise ValueError(f"Unknown operator: {operator}")
            else:
                clone._filters.append((key, "=", value))
        
        return clone
    
    def exclude(self, **kwargs) -> "QuerySet[T]":
        """Exclude records matching conditions."""
        clone = self._clone()
        for key, value in kwargs.items():
            if "__" in key:
                parts = key.split("__")
                field = parts[0]
                # Invert the operator
                clone._filters.append((field, "!=", value))
            else:
                clone._filters.append((key, "!=", value))
        return clone
    
    def order_by(self, *fields: str) -> "QuerySet[T]":
        """Order results by fields. Prefix with '-' for descending."""
        clone = self._clone()
        for field in fields:
            if field.startswith("-"):
                clone._order_by.append((field[1:], "DESC"))
            else:
                clone._order_by.append((field, "ASC"))
        return clone
    
    def limit(self, count: int) -> "QuerySet[T]":
        """Limit the number of results."""
        clone = self._clone()
        clone._limit = count
        return clone
    
    def offset(self, count: int) -> "QuerySet[T]":
        """Offset the results."""
        clone = self._clone()
        clone._offset = count
        return clone
    
    def first(self) -> Optional[T]:
        """Get the first result."""
        results = self.limit(1)._execute()
        return results[0] if results else None
    
    def last(self) -> Optional[T]:
        """Get the last result."""
        clone = self._clone()
        if not clone._order_by:
            clone._order_by.append(("id", "DESC"))
        else:
            # Reverse all orderings
            clone._order_by = [
                (field, "ASC" if order == "DESC" else "DESC")
                for field, order in clone._order_by
            ]
        results = clone.limit(1)._execute()
        return results[0] if results else None
    
    def count(self) -> int:
        """Count the number of matching records."""
        sql, params = self._build_sql(count_only=True)
        db = self.model.get_database()
        result = db.execute(sql, params)
        return result[0][0] if result else 0
    
    def exists(self) -> bool:
        """Check if any records match."""
        return self.count() > 0
    
    def all(self) -> List[T]:
        """Get all results as a list."""
        return self._execute()
    
    def values(self, *fields: str) -> List[dict]:
        """Get results as dictionaries with specified fields."""
        results = self._execute()
        if not fields:
            return [item.to_dict() for item in results]
        return [{f: getattr(item, f) for f in fields} for item in results]
    
    def values_list(self, *fields: str, flat: bool = False) -> List[Any]:
        """Get results as tuples or flat list."""
        results = self._execute()
        if flat and len(fields) == 1:
            return [getattr(item, fields[0]) for item in results]
        return [tuple(getattr(item, f) for f in fields) for item in results]
    
    def delete(self) -> int:
        """Delete all matching records."""
        sql, params = self._build_delete_sql()
        db = self.model.get_database()
        db.execute(sql, params)
        # Return approximate count (would need to track affected rows)
        return 0
    
    def update(self, **kwargs) -> int:
        """Update all matching records."""
        if not kwargs:
            return 0
        
        sql, params = self._build_update_sql(kwargs)
        db = self.model.get_database()
        db.execute(sql, params)
        return 0
    
    def _build_sql(self, count_only: bool = False) -> Tuple[str, Tuple]:
        """Build the SQL query."""
        table_name = self.model.get_table_name()
        
        if count_only:
            sql = f"SELECT COUNT(*) FROM {table_name}"
        else:
            sql = f"SELECT * FROM {table_name}"
        
        params = []
        
        # WHERE clause
        if self._filters:
            conditions = []
            for field, operator, value in self._filters:
                if operator == "IN":
                    placeholders = ", ".join("?" * len(value))
                    conditions.append(f"{field} IN ({placeholders})")
                    params.extend(value)
                elif operator in ("IS NULL", "IS NOT NULL"):
                    conditions.append(f"{field} {operator}")
                else:
                    conditions.append(f"{field} {operator} ?")
                    params.append(value)
            
            sql += " WHERE " + " AND ".join(conditions)
        
        # ORDER BY clause
        if self._order_by and not count_only:
            orders = [f"{field} {direction}" for field, direction in self._order_by]
            sql += " ORDER BY " + ", ".join(orders)
        
        # LIMIT and OFFSET
        if self._limit is not None and not count_only:
            sql += f" LIMIT {self._limit}"
        
        if self._offset is not None and not count_only:
            sql += f" OFFSET {self._offset}"
        
        return sql, tuple(params)
    
    def _build_delete_sql(self) -> Tuple[str, Tuple]:
        """Build DELETE SQL query."""
        table_name = self.model.get_table_name()
        sql = f"DELETE FROM {table_name}"
        
        params = []
        
        if self._filters:
            conditions = []
            for field, operator, value in self._filters:
                if operator in ("IS NULL", "IS NOT NULL"):
                    conditions.append(f"{field} {operator}")
                else:
                    conditions.append(f"{field} {operator} ?")
                    params.append(value)
            
            sql += " WHERE " + " AND ".join(conditions)
        
        return sql, tuple(params)
    
    def _build_update_sql(self, updates: dict) -> Tuple[str, Tuple]:
        """Build UPDATE SQL query."""
        table_name = self.model.get_table_name()
        
        sets = []
        params = []
        
        for field, value in updates.items():
            sets.append(f"{field} = ?")
            params.append(value)
        
        sql = f"UPDATE {table_name} SET " + ", ".join(sets)
        
        if self._filters:
            conditions = []
            for field, operator, value in self._filters:
                if operator in ("IS NULL", "IS NOT NULL"):
                    conditions.append(f"{field} {operator}")
                else:
                    conditions.append(f"{field} {operator} ?")
                    params.append(value)
            
            sql += " WHERE " + " AND ".join(conditions)
        
        return sql, tuple(params)
    
    def _execute(self) -> List[T]:
        """Execute the query and return results."""
        if self._cache is not None:
            return self._cache
        
        sql, params = self._build_sql()
        db = self.model.get_database()
        rows = db.execute(sql, params)
        
        results = [self.model._deserialize_row(row) for row in rows]
        self._cache = results
        return results
    
    def __iter__(self) -> Iterator[T]:
        """Iterate over results."""
        return iter(self._execute())
    
    def __len__(self) -> int:
        """Get the count of results."""
        return len(self._execute())
    
    def __getitem__(self, index: Any) -> Any:
        """Support indexing and slicing."""
        if isinstance(index, slice):
            clone = self._clone()
            if index.start is not None:
                clone._offset = (clone._offset or 0) + index.start
            if index.stop is not None:
                clone._limit = index.stop - (index.start or 0)
            return clone._execute()
        return self._execute()[index]
    
    def __bool__(self) -> bool:
        """Check if query has results."""
        return self.exists()
    
    def __repr__(self) -> str:
        return f"<QuerySet({self.model.__name__})>"
