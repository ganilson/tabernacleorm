"""
CLI commands implementation.
"""

import sys
import os
import asyncio
import importlib 
import importlib.util

from ..migrations.generator import MigrationGenerator
from ..migrations.executor import MigrationExecutor
from .shell import run_shell
from .visuals import print_success, print_error, print_warning, print_info

def load_app():
    """Attempt to load the user's application/config."""
    # Add CWD to path
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)
    
    # Check for DATABASE_URL env var
    from ..core.connection import connect, get_connection
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        print_info(f"Using DATABASE_URL from environment.")
        connect(env_url)
    
    potential_files = ["config.py", "app.py", "main.py", "models.py", "wsgi.py", "asgi.py"]
    found = False
    for f in potential_files:
        if os.path.exists(f):
            print_info(f"Loading {f}...")
            # We use importlib to load it as a module
            module_name = f.replace(".py", "")
            try:
                # Clear from sys.modules to force reload if needed
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                
                mod = importlib.import_module(module_name)
                found = True
                
                # Look for DATABASE_URL or a connection object
                url = None
                if hasattr(mod, "DATABASE_URL"):
                    url = mod.DATABASE_URL
                elif hasattr(mod, "settings") and hasattr(mod.settings, "DATABASE_URL"):
                    url = mod.settings.DATABASE_URL
                
                if url and not get_connection():
                    print_info(f"Found DATABASE_URL in {f}, connecting...")
                    connect(url)
                    
            except Exception as e:
                print_warning(f"Failed to load {f}: {e}")
    if not found and not env_url and not get_connection():
        print_warning("No application entry point or DATABASE_URL found. Models might not be detected.")

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
