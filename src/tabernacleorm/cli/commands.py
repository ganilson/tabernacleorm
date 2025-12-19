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
from .visuals import print_success, print_error, print_warning, print_info

def load_app():
    """Attempt to load the user's application/config."""
    # Look for app.py or main.py to load config/models
    # Ideally should be configured via a setting
    sys.path.insert(0, os.getcwd())
    
    potential_files = ["app.py", "main.py", "config.py", "wsgi.py", "asgi.py"]
    found = False
    for f in potential_files:
        if os.path.exists(f):
            print_info(f"Loading {f}...")
            spec = importlib.util.spec_from_file_location("user_app", f)
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                found = True
            except Exception as e:
                print_warning(f"Failed to load {f}: {e}")
    if not found:
        print_warning("No application entry point found. Models might not be detected.")

async def init_project():
    """Initialize a new TabernacleORM project."""
    print_info("Initializing TabernacleORM project...")
    os.makedirs("migrations", exist_ok=True)
    with open("migrations/__init__.py", "w") as f:
        pass
    print_success("Created migrations directory.")

async def makemigrations(name: str):
    """Create a new migration."""
    load_app()
    generator = MigrationGenerator()
    await generator.generate(name)

async def migrate():
    """Apply migrations."""
    load_app()
    executor = MigrationExecutor()
    try:
        await executor.migrate()
        print_success("Migrations applied successfully!")
    except Exception as e:
        print_error(f"Migration failed: {e}")

async def rollback():
    """Rollback last migration."""
    load_app()
    executor = MigrationExecutor()
    await executor.rollback()

async def shell():
    """Start interactive shell."""
    load_app()
    await run_shell()
