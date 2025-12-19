
import pytest
from tabernacleorm import Model, fields

class User(Model):
    __collection__ = "users"
    name = fields.StringField(required=True)
    email = fields.StringField(unique=True)
    age = fields.IntegerField(default=18)
    
@pytest.mark.asyncio
async def test_create_user(db):
    """Test creating a user."""
    # Ensure table exists (usually migrations handle this, but for tests we might need manual setup or auto-creation helper)
    # The current sqlite engine createCollection is what we need
    await db.engine.createCollection("users", {
        "name": {"type": "string", "required": True},
        "email": {"type": "string", "unique": True},
        "age": {"type": "integer"}
    })
    
    user = await User.create(name="John Doe", email="john@example.com")
    assert user.id is not None
    assert user.name == "John Doe"
    assert user.age == 18 # default
    assert not user.is_new

@pytest.mark.asyncio
async def test_find_one(db):
    """Test finding a user."""
    # Setup
    await db.engine.createCollection("users", {"name": {"type": "string"}})
    await User.create(name="Alice")
    
    # Test findOne
    user = await User.findOne({"name": "Alice"})
    assert user is not None
    assert user.name == "Alice"
    
    # Test findById
    byId = await User.findById(user.id)
    assert byId is not None
    assert byId.id == user.id

@pytest.mark.asyncio
async def test_update(db):
    """Test updating a user."""
    await db.engine.createCollection("users", {"name": {"type": "string"}, "age": {"type": "integer"}})
    user = await User.create(name="Bob", age=20)
    
    # Update instance
    user.age = 21
    await user.save()
    
    # Verify DB
    saved = await User.findById(user.id)
    assert saved.age == 21
    
    # Update via QuerySet
    await User.find({"name": "Bob"}).update({"$set": {"age": 22}})
    saved = await User.findById(user.id)
    assert saved.age == 22

@pytest.mark.asyncio
async def test_delete(db):
    """Test deleting a user."""
    await db.engine.createCollection("users", {"name": {"type": "string"}})
    user = await User.create(name="Charlie")
    
    await user.delete()
    
    found = await User.findById(user.id)
    assert found is None

@pytest.mark.asyncio
async def test_validation(db):
    """Test validation errors."""
    with pytest.raises(ValueError):
        user = User(name=None) # Required field
        user.validate()
