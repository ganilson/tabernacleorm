"""
Migration generator for TabernacleORM.
Detects changes in models and generates migration files.
"""

import os
from datetime import datetime
import tabernacleorm

class MigrationGenerator:
    """
    Generates migration files by inspecting models.
    """
    
    def __init__(self, migration_dir: str = "migrations"):
        self.migration_dir = migration_dir
        
    def generate(self, name: str, message: str = "auto generated"):
        """
        Generate a new migration file.
        For now, this creates a template. Detecting schema changes is complex.
        """
        if not os.path.exists(self.migration_dir):
            os.makedirs(self.migration_dir)
            with open(os.path.join(self.migration_dir, "__init__.py"), "w") as f:
                pass
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{name}.py"
        path = os.path.join(self.migration_dir, filename)
        
        content = f"""from tabernacleorm.migrations import Migration

class Migration_{timestamp}(Migration):
    def up(self):
        # self.create_collection("users", {{
        #     "name": {{"type": "string", "required": True}}
        # }})
        pass
        
    def down(self):
        # self.drop_collection("users")
        pass
"""
        
        with open(path, "w") as f:
            f.write(content)
            
        print(f"Created migration: {path}")
