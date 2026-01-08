"""
Models module for TabernacleORM.
"""

from .model import Model, EmbeddedModel

from .hooks import hook

__all__ = ["Model", "EmbeddedModel", "hook"]
