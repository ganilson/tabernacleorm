
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from tabernacleorm import connect, disconnect
from tabernacleorm.core.connection import Connection
from tabernacleorm.core.config import Config

# Mock engines to avoid real database connections
class MockEngine:
    def __init__(self, config):
        self.config = config
        self.connected = False
        
    async def connect(self):
        self.connected = True
        
    async def disconnect(self):
        self.connected = False
        
    async def insertOne(self, *args, **kwargs): return "new_id"
    async def findOne(self, *args, **kwargs): return {"id": "1"}

@pytest.mark.asyncio
async def test_mongodb_replica_set_config():
    """Test MongoDB connection with replica set parameters."""
    await disconnect() # Ensure clean state
    try:
        with patch("tabernacleorm.core.connection.Connection._get_engine_class") as mock_get_cls:
            mock_get_cls.return_value = MockEngine
            
            db = connect(
                url="mongodb://localhost:27017/db",
                replica_set="rs0",
                read_preference="secondary"
            )
            await db.connect()
            
            # Verify write engine config
            write_engine = db.get_write_engine()
            assert write_engine.config.replica_set == "rs0"
            assert write_engine.config.read_preference == "secondary"
            assert write_engine.connected
    finally:
        await disconnect()

@pytest.mark.asyncio
async def test_read_write_splitting_postgresql():
    """Test Postgres read/write splitting configuration."""
    await disconnect()
    try:
        with patch("tabernacleorm.core.connection.Connection._get_engine_class") as mock_get_cls:
            mock_get_cls.return_value = MockEngine
            
            db = connect(
                engine="postgresql",
                write={"url": "postgresql://master:5432/db"},
                read=[
                    {"url": "postgresql://slave1:5432/db"},
                    {"url": "postgresql://slave2:5432/db"}
                ]
            )
            await db.connect()
            
            # Verify Write Engine
            write_engine = db.get_write_engine()
            assert "master" in write_engine.config.url
            assert write_engine.connected
            
            # Verify Read Engines
            # Access protected member for testing
            read_engines = db._read_engines
            assert len(read_engines) == 2
            
            read1 = db.get_read_engine()
            read2 = db.get_read_engine()
            read3 = db.get_read_engine()
            
            # Check round-robin distribution
            urls = [read1.config.url, read2.config.url, read3.config.url]
            assert any("slave1" in u for u in urls)
            assert any("slave2" in u for u in urls)
            
            # Verify round robin logic actually rotated
            assert read1.config.url != read2.config.url or len(read_engines) == 1
            assert read1.config.url == read3.config.url
    finally:
        await disconnect()

@pytest.mark.asyncio
async def test_mysql_replicas():
    """Test MySQL read/write splitting."""
    await disconnect()
    try:
        with patch("tabernacleorm.core.connection.Connection._get_engine_class") as mock_get_cls:
            mock_get_cls.return_value = MockEngine
            
            db = connect(
                engine="mysql",
                write={"url": "mysql://master:3306/db"},
                read=[
                    {"url": "mysql://replica1:3306/db"}
                ]
            )
            await db.connect()
            
            write_eng = db.get_write_engine()
            assert "master" in write_eng.config.url
            
            read_eng = db.get_read_engine()
            assert "replica1" in read_eng.config.url
    finally:
        await disconnect()

@pytest.mark.asyncio
async def test_sqlite_replicas_simulation():
    """Test SQLite 'replica' (read-only file) simulation."""
    await disconnect()
    try:
        with patch("tabernacleorm.core.connection.Connection._get_engine_class") as mock_get_cls:
            mock_get_cls.return_value = MockEngine
            
            db = connect(
                engine="sqlite",
                write={"url": "sqlite:///primary.db"},
                read=[{"url": "sqlite:///readonly_replica.db"}]
            )
            await db.connect()
            
            assert "primary.db" in db.get_write_engine().config.url
            assert "readonly_replica.db" in db.get_read_engine().config.url
    finally:
        await disconnect()

@pytest.mark.asyncio
async def test_failover_logic_config_check():
    """Test that explicit nodes configuration is stored correctly for failover logic."""
    await disconnect()
    try:
        with patch("tabernacleorm.core.connection.Connection._get_engine_class") as mock_get_cls:
            mock_get_cls.return_value = MockEngine
            
            nodes = ["mongodb://n1", "mongodb://n2"]
            db = connect(
                engine="mongodb",
                nodes=nodes,
                auto_failover=True
            )
            await db.connect()
            
            config = db.get_write_engine().config
            assert len(config.nodes) == 2
            assert config.nodes[0].url == "mongodb://n1"
            assert config.auto_failover is True
    finally:
        await disconnect()
