"""
Models module for TabernacleORM.
"""

from .model import Model, EmbeddedModel
from .meta import ModelMeta
from .hooks import hook

__all__ = ["Model", "EmbeddedModel", "ModelMeta", "hook"]
