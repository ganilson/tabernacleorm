"""
Connection management for TabernacleORM.

Provides a unified interface for connecting to different database engines.
"""

from typing import Any, Dict, List, Optional, Type, Union
import re

from .config import Config

# Global connection instance
_connection: Optional["Connection"] = None


import random

class Connection:
    """
    Database connection manager.
    
    Handles connection pooling, read/write splitting, and engine routing.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self._engine = None
        self._write_engine = None
        self._read_engines: List[Tuple[Any, int]] = [] # engine, weight
        self._connected = False
    
    async def connect(self) -> None:
        """Establish database connection(s)."""
        if self._connected:
            return
        
        engine_class = self._get_engine_class()
        
        # Setup write connection
        write_config = self.config.get_write_config()
        self._write_engine = engine_class(write_config)
        await self._write_engine.connect()
        
        # Setup read connections (if read/write splitting enabled)
        read_configs = self.config.get_read_configs()
        if self.config.read:
            for read_config in read_configs:
                engine = engine_class(read_config)
                await engine.connect()
                self._read_engines.append((engine, read_config.weight))
        
        # Default engine is write engine
        self._engine = self._write_engine
        self._connected = True

        # Auto Schema Creation
        if getattr(self, "_auto_create", False):
            # We need to discover all registered models and create their tables.
            # Importing registry here to avoid circular imports?
            # Or assume models are imported.
            from .registry import _model_registry
            if _model_registry:
                # We need to be careful with relationships/foreign key ordering.
                # Simplest way: create all, rely on 'IF NOT EXISTS' or engine handling.
                # However, FKs require target table to exist.
                # A topological sort would be best, or multiple passes.
                # For this iteration: just linear iteration.
                # It catches most simple cases.
                for model_name, model_cls in _model_registry.items():
                    if hasattr(model_cls, "create_table"):
                         await model_cls.create_table(safe=True)
    
    async def disconnect(self) -> None:
        """Close all database connections."""
        if self._write_engine:
            await self._write_engine.disconnect()
        
        for engine, _ in self._read_engines:
            await engine.disconnect()
        
        self._connected = False
    
    def _get_engine_class(self) -> Type:
        """Get the appropriate engine class based on config."""
        engine_name = self.config.engine
        print(f"DEBUG: Engine name detected: '{engine_name}' for URL: '{self.config.url}'")
        
        if engine_name == "sqlite":
            from ..engines.sqlite import SQLiteEngine
            return SQLiteEngine
        elif engine_name == "postgresql":
            from ..engines.postgresql import PostgreSQLEngine
            return PostgreSQLEngine
        elif engine_name == "mysql":
            from ..engines.mysql import MySQLEngine
            return MySQLEngine
        elif engine_name == "mongodb":
            from ..engines.mongodb import MongoDBEngine
            return MongoDBEngine
        else:
            raise ValueError(f"Unsupported engine: {engine_name}")

    def get_write_engine(self):
        """Get engine for write operations."""
        return self._write_engine
    
    def get_read_engine(self):
        """Get engine for read operations (load balanced)."""
        if not self._read_engines:
            return self._write_engine
        
        # Weighted Load Balancing
        engines, weights = zip(*self._read_engines)
        return random.choices(engines, weights=weights, k=1)[0]
    
    @property
    def engine(self):
        """Get the appropriate engine (read or write) based on context preference."""
        from ..decorators import get_read_preference
        pref = get_read_preference()
        if pref and pref != 'primary':
            return self.get_read_engine()
        return self._engine
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to database."""
        return self._connected


def connect(
    url: Optional[str] = None,
    *,
    engine: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    database: Optional[str] = None,
    pool_size: int = 10,
    timeout: int = 30,
    echo: bool = False,
    ssl: bool = False,
    ssl_mode: Optional[str] = None,
    # MongoDB specific
    auth_source: Optional[str] = None,
    retry_writes: bool = True,
    write_concern: str = "majority",
    read_preference: str = "primary",
    replica_set: Optional[str] = None,
    # MySQL specific
    charset: str = "utf8mb4",
    autocommit: bool = False,
    # SQLite specific
    check_same_thread: bool = False,
    # Multi-node
    nodes: Optional[List[Dict]] = None,
    auto_failover: bool = True,
    # Read/Write splitting
    write: Optional[Dict[str, Any]] = None,
    read: Optional[List[Dict[str, Any]]] = None,
    # UUID
    # UUID
    uuid_storage: str = "string",
    # Auto-Schema
    auto_create: bool = False,
    **kwargs
) -> Connection:
    """
    Connect to a database.
    
    Simple mode (auto-detect engine):
    ...
    Args:
        ...
        auto_create: Automatically create tables for all registered models on connect.
    """
    global _connection
    
    # Build config
    if url and not engine:
        config = Config.from_url(url)
    else:
        config = Config(url=url, engine=engine)
    
    # Apply all options
    config.user = user or config.user
    config.password = password or config.password
    config.database = database or config.database
    config.pool_size = pool_size
    config.timeout = timeout
    config.echo = echo
    config.ssl = ssl
    config.ssl_mode = ssl_mode
    config.auth_source = auth_source
    config.retry_writes = retry_writes
    config.write_concern = write_concern
    config.read_preference = read_preference
    config.replica_set = replica_set
    config.charset = charset
    config.autocommit = autocommit
    config.check_same_thread = check_same_thread
    config.auto_failover = auto_failover
    config.uuid_storage = uuid_storage
    config.write = write
    config.read = read
    
    # Handle nodes
    if nodes:
        from .config import DatabaseNode
        config.nodes = [
            DatabaseNode(**n) if isinstance(n, dict) else DatabaseNode(url=n)
            for n in nodes
        ]
    
    # Create and store connection
    _connection = Connection(config)
    
    # We can't await inside this sync function easily for the user flow 
    # unless usage is: 'await connect(...)'. 
    # But usually 'connect' is async or sync?
    # The user has been doing 'await connect(...)' in examples?
    # BUT wait, the signature of connect() in this file is NOT async. It returns Connection.
    # The actual connection logic is in `Connection.connect()`.
    # Usage: `db = connect(...); await db.connect()`
    # OR helper: `await connect(...).connect()`?
    # Wait, the user's snippet in README says: `connect("...");` then `await User.get_engine()...` 
    # Actually, in README: `connect("sqlite:///:memory:")` is called at module level or top of main.
    # It creates the global connection OBJECT.
    # It does NOT establish connection I/O yet, usually.
    # BaseEngine.connect is async.
    
    # The 'connect' function just creates the manager.
    # Users call `await get_connection().connect()` or the engine handles it lazily?
    # Let's check `Connection.connect`.
    # It has all connection logic.
    
    # So to support auto_create, we must piggyback on `Connection.connect`.
    # We need to pass `auto_create` flag to `Connection` object.
    
    _connection._auto_create = auto_create # Monkey patch or add field
    
    return _connection


async def disconnect() -> None:
    """Disconnect from the database."""
    global _connection
    if _connection:
        await _connection.disconnect()
        _connection = None


def get_connection() -> Optional[Connection]:
    """Get the current database connection."""
    return _connection
