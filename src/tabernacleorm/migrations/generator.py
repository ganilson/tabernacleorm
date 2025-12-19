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
        
    async def generate(self, name: str, message: str = "auto generated"):
        """
        Generate a new migration file based on current models.
        """
        if not os.path.exists(self.migration_dir):
            os.makedirs(self.migration_dir)
            with open(os.path.join(self.migration_dir, "__init__.py"), "w") as f:
                pass
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{name}.py"
        path = os.path.join(self.migration_dir, filename)
        
        # Discover models
        from ..models.model import Model
        models = Model.__subclasses__()
        
        up_operations = []
        down_operations = []
        
        for model in models:
            if model.__module__ == "tabernacleorm.models.model":
                continue 
            
            # Generate schema spec
            schema = {}
            for field_name, field in model._fields.items():
                field_type = "string"
                cls_name = field.__class__.__name__
                
                if "Integer" in cls_name or "ForeignKey" in cls_name:
                    field_type = "integer"
                elif "Boolean" in cls_name:
                    field_type = "boolean"
                elif "Float" in cls_name:
                    field_type = "float"
                elif "Date" in cls_name:
                    field_type = "datetime" if "Time" in cls_name else "date"
                elif "JSON" in cls_name:
                    field_type = "json"
                elif "Array" in cls_name:
                    field_type = "array"
                
                spec = {
                    "type": field_type,
                    "primary_key": field.primary_key,
                    "unique": field.unique,
                    "default": field.default,
                }
                if not field.nullable:
                    spec["required"] = True
                if hasattr(field, "auto_increment") and field.auto_increment:
                    spec["auto_increment"] = True

                schema[field_name] = spec
            
            op = f'        await self.createCollection("{model.__collection__}", {repr(schema)})'
            up_operations.append(op)
            
            down_op = f'        await self.dropCollection("{model.__collection__}")'
            down_operations.append(down_op)
            
        up_content = "\n".join(up_operations)
        down_content = "\n".join(down_operations)
        
        content = f"""from tabernacleorm.migrations import Migration

class Migration_{timestamp}(Migration):
    async def up(self):
{up_content or '        pass'}
        
    async def down(self):
{down_content or '        pass'}
"""
        
        with open(path, "w") as f:
            f.write(content)
            
        from ..cli.visuals import print_success
        print_success(f"Created migration: {path}")

