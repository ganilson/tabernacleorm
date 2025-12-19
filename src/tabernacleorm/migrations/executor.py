"""
Migration executor for TabernacleORM.
"""

import os
import importlib.util
import asyncio
from datetime import datetime
from typing import List, Optional

from ..core.connection import get_connection

class MigrationExecutor:
    """
    Runs migrations.
    """
    
    def __init__(self, migration_dir: str = "migrations"):
        self.migration_dir = migration_dir
        self.connection = get_connection()
    
    async def init_migration_table(self):
        """Create the __migrations table if it doesn't exist."""
        exists = await self.connection.engine.collection_exists("__migrations")
        if not exists:
            await self.connection.engine.create_collection("__migrations", {
                "name": {"type": "string", "primary_key": True},
                "applied_at": {"type": "datetime"}
            })
    
    async def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration names."""
        await self.init_migration_table()
        rows = await self.connection.engine.find_many("__migrations", {}, sort=[("name", 1)])
        return [r["name"] for r in rows]
    
    async def load_migrations(self):
        """Load migration files from directory."""
        if not os.path.exists(self.migration_dir):
            return []
            
        files = sorted([f for f in os.listdir(self.migration_dir) if f.endswith(".py") and f != "__init__.py"])
        migrations = []
        
        for f in files:
            name = f[:-3]
            path = os.path.join(self.migration_dir, f)
            
            # Dynamic import
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find Migration subclass
            migration_cls = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                try:
                    if issubclass(attr, module.Migration) and attr != module.Migration:
                        migration_cls = attr
                        break
                except TypeError:
                    continue
            
            if migration_cls:
                migrations.append((name, migration_cls))
                
        return migrations
    
    async def migrate(self):
        """Run all pending migrations."""
        applied = set(await self.get_applied_migrations())
        all_migrations = await self.load_migrations()
        
        for name, cls in all_migrations:
            if name not in applied:
                print(f"Applying {name}...")
                migration = cls()
                try:
                    await migration.up()
                    
                    # Record execution
                    # Use current engine's format for datetime if needed
                    now = datetime.now()
                    await self.connection.engine.insert_one("__migrations", {
                        "name": name,
                        "applied_at": now
                    })
                    print(f"Applied {name}.")
                except Exception as e:
                    print(f"Error applying {name}: {e}")
                    raise
    
    async def rollback(self):
        """Rollback the last migration."""
        applied = await self.get_applied_migrations()
        if not applied:
            print("No migrations to rollback.")
            return
            
        last_name = applied[-1]
        all_migrations = await self.load_migrations()
        
        # Find class for last migration
        migration_cls = None
        for name, cls in all_migrations:
            if name == last_name:
                migration_cls = cls
                break
        
        if migration_cls:
            print(f"Rolling back {last_name}...")
            migration = migration_cls()
            try:
                await migration.down()
                await self.connection.engine.delete_one("__migrations", {"name": last_name})
                print(f"Rolled back {last_name}.")
            except Exception as e:
                print(f"Error rolling back {last_name}: {e}")
                raise
