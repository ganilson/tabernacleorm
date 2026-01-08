"""
Simple Global Registry to helper resolve string model references.
"""

from typing import Dict, Type, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from ..models.model import Model

_model_registry: Dict[str, Type["Model"]] = {}

def register_model(name: str, model_cls: Type["Model"]):
    _model_registry[name] = model_cls

def get_model(name: str) -> Optional[Type["Model"]]:
    return _model_registry.get(name)
