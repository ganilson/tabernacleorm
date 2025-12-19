"""
Base Migration class for TabernacleORM.
"""

from typing import Any, Dict, List, Optional
from ..core.connection import get_connection

class Migration:
    """
    Base class for all migrations.
    """
    
    dependencies: List[str] = []
    
    def __init__(self):
        self.connection = get_connection()
    
    @property
    def db(self):
        return self.connection.engine
    
    async def up(self):
        """Apply migration changes."""
        pass
    
    async def down(self):
        """Revert migration changes."""
        pass
    
    @property
    def is_mongodb(self) -> bool:
        """Check if current engine is MongoDB."""
        return self.db.__class__.__name__ == "MongoDBEngine"

    async def createCollection(self, name: str, schema: Optional[Dict] = None):
        """Create a collection/table."""
        if self.is_mongodb:
            return 
        await self.db.createCollection(name, schema)
    
    async def dropCollection(self, name: str):
        """Drop a collection/table."""
        if self.is_mongodb:
            return
        await self.db.dropCollection(name)
        
    async def createIndex(self, collection: str, fields: List[str], unique: bool = False):
        """Create an index."""
        if self.is_mongodb:
            return
        await self.db.createIndex(collection, fields, unique=unique)
        
    async def dropIndex(self, collection: str, name: str):
        """Drop an index."""
        if self.is_mongodb:
            return
        await self.db.dropIndex(collection, name)
        
    async def execute(self, sql: str, params: Optional[tuple] = None):
        """Execute raw SQL."""
        if self.is_mongodb:
            return
        await self.db.executeRaw(sql, params)
