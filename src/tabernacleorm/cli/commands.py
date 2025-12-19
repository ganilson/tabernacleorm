"""
CLI commands implementation.
"""

import sys
import os
import asyncio
import importlib.util

from ..migrations.generator import MigrationGenerator
from ..migrations.executor import MigrationExecutor
from .shell import run_shell

def load_app():
    """Attempt to load the user's application/config."""
    # Look for app.py or main.py to load config/models
    # Ideally should be configured via a setting
    sys.path.insert(0, os.getcwd())
    
    potential_files = ["app.py", "main.py", "config.py", "wsgi.py", "asgi.py"]
    for f in potential_files:
        if os.path.exists(f):
            print(f"Loading {f}...")
            spec = importlib.util.spec_from_file_location("user_app", f)
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
            except Exception as e:
                print(f"Warning: Failed to load {f}: {e}")

async def init_project():
    """Initialize a new TabernacleORM project."""
    print("Initializing TabernacleORM project...")
    os.makedirs("migrations", exist_ok=True)
    with open("migrations/__init__.py", "w") as f:
        pass
    print("Created migrations directory.")

async def makemigrations(name: str):
    """Create a new migration."""
    generator = MigrationGenerator()
    generator.generate(name)

async def migrate():
    """Apply migrations."""
    load_app()
    executor = MigrationExecutor()
    await executor.migrate()

async def rollback():
    """Rollback last migration."""
    load_app()
    executor = MigrationExecutor()
    await executor.rollback()

async def shell():
    """Start interactive shell."""
    load_app()
    await run_shell()
