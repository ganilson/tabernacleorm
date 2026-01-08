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
        processed_models = set()
        
        for model in models:
            if model.__module__ == "tabernacleorm.models.model":
                continue 
            
            table_name = model.get_table_name()
            if table_name in processed_models:
                continue
            processed_models.add(table_name)
            schema = {}
            for field_name, field_info in model.model_fields.items():
                extra = field_info.json_schema_extra or {}
                # Skip relationships
                if "relationship" in extra:
                    continue
                    
                tab_args = extra.get("tabernacle_args", {})
                field_type = "string"
                
                # Try to infer type from python type hint if not explicit
                annotation = field_info.annotation
                if str(annotation) == "int":
                    field_type = "integer"
                elif str(annotation) == "bool":
                    field_type = "boolean"
                elif str(annotation) == "float":
                    field_type = "float"
                
                # Override with explicit tabernacle type if present
                if "type" in tab_args:
                    field_type = tab_args["type"]
                
                spec = {
                    "type": field_type,
                    "primary_key": tab_args.get("primary_key", False),
                    "unique": tab_args.get("unique", False),
                    "default": tab_args.get("default"),
                }
                if tab_args.get("nullable") is False:
                    spec["required"] = True
                if tab_args.get("auto_increment"):
                    spec["auto_increment"] = True

                schema[field_name] = spec
            
            op = f'        await self.createCollection("{table_name}", {repr(schema)})'
            up_operations.append(op)
            
            down_op = f'        await self.dropCollection("{table_name}")'
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

