"""
Connection management for TabernacleORM.

Provides a unified interface for connecting to different database engines.
"""

from typing import Any, Dict, List, Optional, Type, Union
import re

from .config import Config

# Global connection instance
_connection: Optional["Connection"] = None


class Connection:
    """
    Database connection manager.
    
    Handles connection pooling, read/write splitting, and engine routing.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self._engine = None
        self._write_engine = None
        self._read_engines: List = []
        self._read_index = 0
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
                self._read_engines.append(engine)
        
        # Default engine is write engine
        self._engine = self._write_engine
        self._connected = True
    
    async def disconnect(self) -> None:
        """Close all database connections."""
        if self._write_engine:
            await self._write_engine.disconnect()
        
        for engine in self._read_engines:
            await engine.disconnect()
        
        self._connected = False
    
    def _get_engine_class(self) -> Type:
        """Get the appropriate engine class based on config."""
        engine_name = self.config.engine
        
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
        
        # Simple round-robin load balancing
        # TODO: Implement weight-based selection
        engine = self._read_engines[self._read_index % len(self._read_engines)]
        self._read_index += 1
        return engine
    
    @property
    def engine(self):
        """Get the default engine."""
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
    uuid_storage: str = "string",
    **kwargs
) -> Connection:
    """
    Connect to a database.
    
    Simple mode (auto-detect engine):
        db = connect("mongodb://localhost:27017/myapp")
        db = connect("postgresql://user:pass@localhost:5432/myapp")
        db = connect("sqlite:///./myapp.db")
    
    Advanced mode (explicit engine + options):
        db = connect(
            url="localhost:5432/myapp",
            engine="postgresql",
            user="admin",
            password="secret",
            pool_size=20,
            echo=True,
        )
    
    Replica set mode:
        db = connect(
            engine="mongodb",
            replica_set="myReplicaSet",
            nodes=[
                "mongodb://node1:27017",
                "mongodb://node2:27017",
            ],
            database="myapp",
        )
    
    Read/Write splitting:
        db = connect(
            engine="postgresql",
            write={"url": "postgresql://master:5432/db"},
            read=[
                {"url": "postgresql://replica1:5432/db", "weight": 70},
                {"url": "postgresql://replica2:5432/db", "weight": 30},
            ],
        )
    
    Args:
        url: Database connection URL
        engine: Database engine (mongodb, postgresql, mysql, sqlite)
        user: Database user
        password: Database password
        database: Database name
        pool_size: Connection pool size
        timeout: Connection timeout in seconds
        echo: Log SQL/queries to console
        ssl: Enable SSL
        ssl_mode: SSL mode (require, verify-ca, verify-full)
        auth_source: MongoDB auth database
        retry_writes: MongoDB retry writes
        write_concern: MongoDB write concern
        read_preference: MongoDB read preference
        replica_set: MongoDB replica set name
        charset: MySQL charset
        autocommit: Auto-commit mode for SQL databases
        check_same_thread: SQLite multi-threading
        nodes: List of database nodes for replica sets
        auto_failover: Enable automatic failover
        write: Write database configuration
        read: Read database(s) configuration
        uuid_storage: UUID storage format (string, binary)
    
    Returns:
        Connection instance
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
