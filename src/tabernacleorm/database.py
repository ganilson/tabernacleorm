"""
Database connection and management for TabernacleORM.
"""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Type
from contextlib import contextmanager


class Database:
    """Database connection manager."""
    
    _instance: Optional["Database"] = None
    _connection: Optional[sqlite3.Connection] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        database: str = ":memory:",
        echo: bool = False,
    ):
        self.database = database
        self.echo = echo
        self._models: Dict[str, Type] = {}
    
    def connect(self) -> sqlite3.Connection:
        """Establish database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.database)
            self._connection.row_factory = sqlite3.Row
            if self.echo:
                print(f"Connected to database: {self.database}")
        return self._connection
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            if self.echo:
                print("Disconnected from database")
    
    @property
    def connection(self) -> sqlite3.Connection:
        """Get or create connection."""
        return self.connect()
    
    @contextmanager
    def cursor(self):
        """Context manager for database cursor."""
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def execute(
        self, sql: str, params: Optional[Tuple] = None
    ) -> List[sqlite3.Row]:
        """Execute SQL query and return results."""
        if self.echo:
            print(f"SQL: {sql}")
            if params:
                print(f"Params: {params}")
        
        with self.cursor() as cursor:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.fetchall()
    
    def execute_many(
        self, sql: str, params_list: List[Tuple]
    ) -> None:
        """Execute SQL query with multiple parameter sets."""
        if self.echo:
            print(f"SQL: {sql}")
            print(f"Batch size: {len(params_list)}")
        
        with self.cursor() as cursor:
            cursor.executemany(sql, params_list)
    
    def last_insert_id(self) -> int:
        """Get the last inserted row ID."""
        with self.cursor() as cursor:
            cursor.execute("SELECT last_insert_rowid()")
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def register_model(self, model: Type) -> None:
        """Register a model with the database."""
        table_name = model.get_table_name()
        self._models[table_name] = model
    
    def create_tables(self) -> None:
        """Create all registered model tables."""
        for model in self._models.values():
            self.create_table(model)
    
    def create_table(self, model: Type) -> None:
        """Create table for a specific model."""
        from .model import Model
        
        if not issubclass(model, Model):
            raise TypeError("model must be a subclass of Model")
        
        sql = model.get_create_table_sql()
        self.execute(sql)
        
        if self.echo:
            print(f"Created table: {model.get_table_name()}")
    
    def drop_table(self, model: Type) -> None:
        """Drop table for a specific model."""
        from .model import Model
        
        if not issubclass(model, Model):
            raise TypeError("model must be a subclass of Model")
        
        table_name = model.get_table_name()
        sql = f"DROP TABLE IF EXISTS {table_name}"
        self.execute(sql)
        
        if self.echo:
            print(f"Dropped table: {table_name}")
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        sql = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """
        result = self.execute(sql, (table_name,))
        return len(result) > 0
    
    @classmethod
    def get_instance(cls) -> Optional["Database"]:
        """Get the current database instance."""
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance."""
        if cls._instance is not None:
            cls._instance.disconnect()
        cls._instance = None
        cls._connection = None
