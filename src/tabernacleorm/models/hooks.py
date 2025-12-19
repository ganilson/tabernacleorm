"""
Lifecycle hooks for TabernacleORM models.
"""

import functools
from typing import Callable, List, Dict, Any, Type, Optional


class Hooks:
    """Registry for model hooks."""
    
    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = {
            "pre_save": [],
            "post_save": [],
            "pre_insert": [],
            "post_insert": [],
            "pre_update": [],
            "post_update": [],
            "pre_delete": [],
            "post_delete": [],
            "pre_validate": [],
            "post_validate": [],
            "post_find": [],
        }
    
    def register(self, event: str, func: Callable):
        """Register a hook function."""
        if event not in self._hooks:
            raise ValueError(f"Invalid hook event: {event}")
        self._hooks[event].append(func)
    
    async def run(self, event: str, instance: Any):
        """Run all hooks for an event."""
        if event not in self._hooks:
            return
        
        for func in self._hooks[event]:
            # Support both async and sync hooks
            if hasattr(instance, func.__name__):
                # If it's a method name string stored in __hooks__ dict
                pass
            
            # Check if func is a bound method of instance or independent function
            if hasattr(func, "__get__"):
                 # It's a method, bind it to instance
                 # This logic is tricky because decorators on methods are unbound
                 pass
            
            # Simplified approach: assume hooks are methods on the instance
            if asyncio.iscoroutinefunction(func):
                await func(instance)
            else:
                func(instance)


def hook(event: str):
    """
    Decorator to register a method as a hook.
    
    @hook("pre_save")
    async def before_save(self):
        ...
    """
    def decorator(func):
        func._hook_event = event
        return func
    return decorator


class HookMixin:
    """Mixin for Model to handle hooks."""
    
    _hooks: Dict[str, List[Callable]]
    
    @classmethod
    def _collect_hooks(cls):
        """Collect hooks from methods decorated with @hook."""
        hooks = {
            "pre_save": [],
            "post_save": [],
            "pre_insert": [],
            "post_insert": [],
            "pre_update": [],
            "post_update": [],
            "pre_delete": [],
            "post_delete": [],
            "pre_validate": [],
            "post_validate": [],
            "post_find": [],
        }
        
        # Check all methods
        for name in dir(cls):
            attr = getattr(cls, name)
            if hasattr(attr, "_hook_event"):
                event = attr._hook_event
                if event in hooks:
                    hooks[event].append(name)
        
        # Check __hooks__ class attribute
        if hasattr(cls, "__hooks__"):
             for event, methods in cls.__hooks__.items():
                 if event in hooks:
                     if isinstance(methods, list):
                         hooks[event].extend(methods)
                     else:
                         hooks[event].append(methods)
        
        return hooks
    
    async def _run_hooks(self, event: str):
        """Execute hooks for an event."""
        if not hasattr(self.__class__, "_hooks_registry"):
            # Should be set by metaclass, but fallback just in case
            self.__class__._hooks_registry = self._collect_hooks()
            
        hooks = self.__class__._hooks_registry.get(event, [])
        for method_name in hooks:
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                import asyncio
                if asyncio.iscoroutinefunction(method):
                    await method()
                else:
                    method()
