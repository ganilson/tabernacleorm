from tabernacleorm.migrations import Migration

class Migration_20260108133756(Migration):
    async def up(self):
        await self.createCollection("users", {'id': {'type': 'integer', 'primary_key': True, 'unique': False, 'default': None, 'auto_increment': True}, 'name': {'type': 'string', 'primary_key': False, 'unique': False, 'default': None}, 'email': {'type': 'string', 'primary_key': False, 'unique': True, 'default': None}, 'created_at': {'type': 'datetime', 'primary_key': False, 'unique': False, 'default': None}})
        await self.createCollection("todo_lists", {'id': {'type': 'integer', 'primary_key': True, 'unique': False, 'default': None, 'auto_increment': True}, 'title': {'type': 'string', 'primary_key': False, 'unique': False, 'default': None}, 'description': {'type': 'string', 'primary_key': False, 'unique': False, 'default': None}, 'created_at': {'type': 'datetime', 'primary_key': False, 'unique': False, 'default': None}, 'updated_at': {'type': 'datetime', 'primary_key': False, 'unique': False, 'default': None}, 'user_id': {'type': 'integer', 'primary_key': False, 'unique': False, 'default': None}})
        await self.createCollection("todo_items", {'id': {'type': 'integer', 'primary_key': True, 'unique': False, 'default': None, 'auto_increment': True}, 'title': {'type': 'string', 'primary_key': False, 'unique': False, 'default': None}, 'description': {'type': 'string', 'primary_key': False, 'unique': False, 'default': None}, 'completed': {'type': 'boolean', 'primary_key': False, 'unique': False, 'default': None}, 'priority': {'type': 'integer', 'primary_key': False, 'unique': False, 'default': None}, 'due_date': {'type': 'datetime', 'primary_key': False, 'unique': False, 'default': None}, 'created_at': {'type': 'datetime', 'primary_key': False, 'unique': False, 'default': None}, 'completed_at': {'type': 'datetime', 'primary_key': False, 'unique': False, 'default': None}, 'list_id': {'type': 'integer', 'primary_key': False, 'unique': False, 'default': None}})
        
    async def down(self):
        await self.dropCollection("users")
        await self.dropCollection("todo_lists")
        await self.dropCollection("todo_items")
