"""
Core module for TabernacleORM.
Contains connection management, configuration, and engine routing.
"""

from .connection import connect, disconnect, get_connection
from .config import Config

__all__ = ["connect", "disconnect", "get_connection", "Config"]
