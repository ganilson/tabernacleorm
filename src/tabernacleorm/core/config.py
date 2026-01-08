"""
Configuration management for TabernacleORM.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field


@dataclass
class DatabaseNode:
    """Configuration for a single database node."""
    
    url: str
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    role: str = "primary"  # primary, replica, secondary
    weight: int = 100  # Load balancing weight for read replicas


@dataclass
class Config:
    """
    Database configuration class.
    
    Supports simple connection strings and advanced multi-node configurations.
    """
    
    # Connection
    url: Optional[str] = None
    engine: Optional[str] = None  # mongodb, postgresql, mysql, sqlite
    
    # Credentials (can also be in URL)
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    
    # Connection pool
    pool_size: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    
    # General options
    timeout: int = 30
    echo: bool = False
    ssl: bool = False
    ssl_mode: Optional[str] = None
    weight: int = 100  # Load balancing weight
    
    # MongoDB specific
    auth_source: Optional[str] = None
    retry_writes: bool = True
    write_concern: str = "majority"
    read_preference: str = "primary"
    
    # MySQL specific
    charset: str = "utf8mb4"
    autocommit: bool = False
    
    # SQLite specific
    check_same_thread: bool = False
    
    # UUID storage
    uuid_storage: str = "string"  # string, binary
    
    # Replica sets / Multi-node
    replica_set: Optional[str] = None
    nodes: List[DatabaseNode] = field(default_factory=list)
    auto_failover: bool = True
    
    # Read/Write splitting
    write: Optional[Dict[str, Any]] = None
    read: Optional[List[Dict[str, Any]]] = None
    
    @classmethod
    def from_url(cls, url: str, **kwargs) -> "Config":
        """
        Create config from connection URL with auto-detection.
        
        Supported URL formats:
        - mongodb://user:pass@host:port/database
        - postgresql://user:pass@host:port/database
        - mysql://user:pass@host:port/database
        - sqlite:///path/to/file.db
        - sqlite:///:memory:
        """
        config = cls(url=url, **kwargs)
        
        # Auto-detect engine from URL if not specified
        if not config.engine:
            config.engine = cls._detect_engine(url)
        
        return config
    
    @staticmethod
    def _detect_engine(url: str) -> str:
        """Detect database engine from URL."""
        url_lower = url.lower()
        
        if url_lower.startswith("mongodb"):
            return "mongodb"
        elif url_lower.startswith("postgresql") or url_lower.startswith("postgres"):
            return "postgresql"
        elif url_lower.startswith("mysql"):
            return "mysql"
        elif url_lower.startswith("sqlite") or url.endswith(".db") or url == ":memory:":
            return "sqlite"
        else:
            raise ValueError(
                f"Cannot detect engine from URL: {url}. "
                "Please specify engine='mongodb|postgresql|mysql|sqlite'"
            )
    
    def get_write_config(self) -> "Config":
        """Get configuration for write operations."""
        if self.write:
            return Config(**{**self.__dict__, **self.write})
        return self
    
    def get_read_configs(self) -> List["Config"]:
        """Get configurations for read operations (load balanced)."""
        if self.read:
            return [Config(**{**self.__dict__, **r}) for r in self.read]
        return [self]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            k: v for k, v in self.__dict__.items()
            if v is not None and not k.startswith("_")
        }
