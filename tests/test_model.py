"""
Tests for TabernacleORM Model and Database.
"""

import pytest
from datetime import datetime
from tabernacleorm import (
    Database,
    Model,
    IntegerField,
    StringField,
    BooleanField,
    DateTimeField,
)


class User(Model):
    name = StringField(max_length=100, nullable=False)
    email = StringField(max_length=255, unique=True)
    age = IntegerField(nullable=True)
    active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)


@pytest.fixture
def db():
    """Create a fresh in-memory database for each test."""
    Database.reset()
    database = Database(":memory:", echo=False)
    User.set_database(database)
    database.create_table(User)
    yield database
    database.disconnect()


class TestModel:
    def test_create_instance(self, db):
        user = User(name="John Doe", email="john@example.com", age=30)
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.age == 30
        assert user.id is None
    
    def test_save_and_get_id(self, db):
        user = User(name="Jane Doe", email="jane@example.com")
        user.save()
        assert user.id is not None
        assert user.id > 0
    
    def test_create_shortcut(self, db):
        user = User.create(name="Bob", email="bob@example.com")
        assert user.id is not None
    
    def test_get_by_id(self, db):
        user = User.create(name="Alice", email="alice@example.com", age=25)
        found = User.get_by_id(user.id)
        assert found is not None
        assert found.name == "Alice"
        assert found.age == 25
    
    def test_get_returns_none(self, db):
        found = User.get(name="Nonexistent")
        assert found is None
    
    def test_update(self, db):
        user = User.create(name="Original", email="orig@example.com")
        user.name = "Updated"
        user.save()
        
        found = User.get_by_id(user.id)
        assert found.name == "Updated"
    
    def test_delete(self, db):
        user = User.create(name="ToDelete", email="delete@example.com")
        user_id = user.id
        user.delete()
        
        found = User.get_by_id(user_id)
        assert found is None
    
    def test_default_values(self, db):
        user = User(name="Test", email="test@example.com")
        assert user.active is True
    
    def test_auto_now_add(self, db):
        user = User.create(name="Timestamp", email="time@example.com")
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)
    
    def test_to_dict(self, db):
        user = User.create(name="Dict", email="dict@example.com", age=40)
        data = user.to_dict()
        assert data["name"] == "Dict"
        assert data["email"] == "dict@example.com"
        assert data["age"] == 40
    
    def test_repr(self, db):
        user = User.create(name="Repr", email="repr@example.com")
        repr_str = repr(user)
        assert "User" in repr_str
        assert str(user.id) in repr_str


class TestQuerySet:
    def test_all(self, db):
        User.create(name="User1", email="user1@example.com")
        User.create(name="User2", email="user2@example.com")
        
        users = User.all()
        assert len(list(users)) == 2
    
    def test_filter(self, db):
        User.create(name="John", email="john@example.com", age=30)
        User.create(name="Jane", email="jane@example.com", age=25)
        
        results = User.filter(age=30)
        users = list(results)
        assert len(users) == 1
        assert users[0].name == "John"
    
    def test_filter_gt(self, db):
        User.create(name="Young", email="young@example.com", age=20)
        User.create(name="Old", email="old@example.com", age=40)
        
        results = User.filter(age__gt=30)
        users = list(results)
        assert len(users) == 1
        assert users[0].name == "Old"
    
    def test_filter_contains(self, db):
        User.create(name="Johnny", email="johnny@example.com")
        User.create(name="Jane", email="jane@example.com")
        
        results = User.filter(name__contains="ohn")
        users = list(results)
        assert len(users) == 1
    
    def test_order_by_asc(self, db):
        User.create(name="B", email="b@example.com", age=30)
        User.create(name="A", email="a@example.com", age=20)
        
        users = list(User.all().order_by("name"))
        assert users[0].name == "A"
        assert users[1].name == "B"
    
    def test_order_by_desc(self, db):
        User.create(name="A", email="a2@example.com", age=20)
        User.create(name="B", email="b2@example.com", age=30)
        
        users = list(User.all().order_by("-name"))
        assert users[0].name == "B"
        assert users[1].name == "A"
    
    def test_limit(self, db):
        for i in range(5):
            User.create(name=f"User{i}", email=f"user{i}@example.com")
        
        users = list(User.all().limit(3))
        assert len(users) == 3
    
    def test_first(self, db):
        User.create(name="First", email="first@example.com")
        User.create(name="Second", email="second@example.com")
        
        user = User.all().order_by("name").first()
        assert user.name == "First"
    
    def test_count(self, db):
        User.create(name="A", email="a3@example.com")
        User.create(name="B", email="b3@example.com")
        User.create(name="C", email="c3@example.com")
        
        assert User.all().count() == 3
    
    def test_exists(self, db):
        assert not User.filter(name="Nobody").exists()
        User.create(name="Somebody", email="some@example.com")
        assert User.filter(name="Somebody").exists()
    
    def test_values(self, db):
        User.create(name="Values", email="values@example.com", age=35)
        
        data = User.filter(name="Values").values("name", "age")
        assert len(data) == 1
        assert data[0]["name"] == "Values"
        assert data[0]["age"] == 35
    
    def test_chaining(self, db):
        User.create(name="A", email="a4@example.com", age=30, active=True)
        User.create(name="B", email="b4@example.com", age=20, active=True)
        User.create(name="C", email="c4@example.com", age=25, active=False)
        
        users = list(
            User.filter(active=True)
            .filter(age__gte=25)
            .order_by("-age")
            .limit(10)
        )
        
        assert len(users) == 1
        assert users[0].name == "A"


class TestDatabase:
    def test_connection(self, db):
        assert db.connection is not None
    
    def test_table_exists(self, db):
        assert db.table_exists("users")
        assert not db.table_exists("nonexistent")
    
    def test_create_drop_table(self, db):
        class TempModel(Model):
            name = StringField(max_length=50)
        
        TempModel.set_database(db)
        db.create_table(TempModel)
        assert db.table_exists("tempmodels")
        
        db.drop_table(TempModel)
        assert not db.table_exists("tempmodels")
