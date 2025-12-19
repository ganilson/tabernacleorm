"""
Simple migrations support for TabernacleORM.
"""

from typing import Dict, List, Optional, Type
from datetime import datetime
from .database import Database


class Migration:
    """Base class for migrations."""
    
    version: str = ""
    description: str = ""
    
    def up(self, db: Database) -> None:
        """Apply the migration."""
        raise NotImplementedError("Subclasses must implement up()")
    
    def down(self, db: Database) -> None:
        """Revert the migration."""
        raise NotImplementedError("Subclasses must implement down()")


class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, db: Database):
        self.db = db
        self._migrations: List[Migration] = []
        self._ensure_migrations_table()
    
    def _ensure_migrations_table(self) -> None:
        """Create migrations tracking table if it doesn't exist."""
        sql = """
            CREATE TABLE IF NOT EXISTS _tabernacle_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                applied_at DATETIME NOT NULL
            )
        """
        self.db.execute(sql)
    
    def register(self, migration: Migration) -> None:
        """Register a migration."""
        self._migrations.append(migration)
        self._migrations.sort(key=lambda m: m.version)
    
    def get_applied_versions(self) -> List[str]:
        """Get list of applied migration versions."""
        sql = "SELECT version FROM _tabernacle_migrations ORDER BY version"
        rows = self.db.execute(sql)
        return [row[0] for row in rows]
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get list of migrations that haven't been applied."""
        applied = set(self.get_applied_versions())
        return [m for m in self._migrations if m.version not in applied]
    
    def apply(self, migration: Migration) -> None:
        """Apply a single migration."""
        migration.up(self.db)
        
        sql = """
            INSERT INTO _tabernacle_migrations (version, description, applied_at)
            VALUES (?, ?, ?)
        """
        self.db.execute(sql, (
            migration.version,
            migration.description,
            datetime.now().isoformat()
        ))
        
        if self.db.echo:
            print(f"Applied migration: {migration.version} - {migration.description}")
    
    def revert(self, migration: Migration) -> None:
        """Revert a single migration."""
        migration.down(self.db)
        
        sql = "DELETE FROM _tabernacle_migrations WHERE version = ?"
        self.db.execute(sql, (migration.version,))
        
        if self.db.echo:
            print(f"Reverted migration: {migration.version}")
    
    def migrate(self) -> int:
        """Apply all pending migrations."""
        pending = self.get_pending_migrations()
        for migration in pending:
            self.apply(migration)
        return len(pending)
    
    def rollback(self, steps: int = 1) -> int:
        """Rollback the last N migrations."""
        applied = self.get_applied_versions()
        to_revert = applied[-steps:] if steps <= len(applied) else applied
        to_revert.reverse()
        
        count = 0
        for version in to_revert:
            migration = next(
                (m for m in self._migrations if m.version == version),
                None
            )
            if migration:
                self.revert(migration)
                count += 1
        
        return count
    
    def reset(self) -> int:
        """Revert all migrations."""
        applied = self.get_applied_versions()
        return self.rollback(len(applied))


def create_migration(version: str, description: str = "") -> Type[Migration]:
    """Factory function to create a migration class."""
    
    class NewMigration(Migration):
        pass
    
    NewMigration.version = version
    NewMigration.description = description
    
    return NewMigration


# Utility functions for common operations
class Schema:
    """Schema builder for migrations."""
    
    @staticmethod
    def create_table(table_name: str, columns: Dict[str, str]) -> str:
        """Generate CREATE TABLE SQL."""
        cols = [f"{name} {definition}" for name, definition in columns.items()]
        return f"CREATE TABLE IF NOT EXISTS {table_name} (\n    " + ",\n    ".join(cols) + "\n)"
    
    @staticmethod
    def drop_table(table_name: str) -> str:
        """Generate DROP TABLE SQL."""
        return f"DROP TABLE IF EXISTS {table_name}"
    
    @staticmethod
    def add_column(table_name: str, column_name: str, column_type: str) -> str:
        """Generate ALTER TABLE ADD COLUMN SQL."""
        return f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
    
    @staticmethod
    def rename_table(old_name: str, new_name: str) -> str:
        """Generate ALTER TABLE RENAME SQL."""
        return f"ALTER TABLE {old_name} RENAME TO {new_name}"
    
    @staticmethod
    def create_index(
        index_name: str,
        table_name: str,
        columns: List[str],
        unique: bool = False
    ) -> str:
        """Generate CREATE INDEX SQL."""
        unique_str = "UNIQUE " if unique else ""
        cols = ", ".join(columns)
        return f"CREATE {unique_str}INDEX IF NOT EXISTS {index_name} ON {table_name} ({cols})"
    
    @staticmethod
    def drop_index(index_name: str) -> str:
        """Generate DROP INDEX SQL."""
        return f"DROP INDEX IF EXISTS {index_name}"
