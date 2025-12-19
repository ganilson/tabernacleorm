"""
Interactive shell for TabernacleORM.
"""

import asyncio
import code
import sys
from ..core.connection import get_connection

async def run_shell():
    """Start the shell."""
    print("TabernacleORM Shell")
    print("Python " + sys.version)
    
    # Setup context
    context = {}
    
    # Add connection and convenience imports
    conn = get_connection()
    if conn:
        print(f"Connected to: {conn.engine.engine_name}")
        context["db"] = conn.engine
    
    # Try to import all models automatically if possible?
    # For now leave it to user to import, or we can scan
    import tabernacleorm
    context["tabernacleorm"] = tabernacleorm
    
    # Use IPython if available
    try:
        from IPython import start_ipython
        # Support async in IPython if possible, but standard IPython doesn't easily support top-level await 
        # without configuration.
        # For now fallback to code.interact but that blocks asyncio loop?
        # Running async code in a synchronous shell is tricky.
        
        # Simple solution: Helper to run async
        def run(coro):
            return asyncio.run(coro)
            
        context["run"] = run
        print("Use run(coro) to execute async functions.")
        
        start_ipython(argv=[], user_ns=context)
        return
    except ImportError:
        pass
        
    def run(coro):
         return asyncio.run(coro)
    context["run"] = run
    print("Use run(coro) to execute async functions.")
    
    code.interact(local=context)
