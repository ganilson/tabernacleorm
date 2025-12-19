"""
Tests for TabernacleORM fields.
"""

import pytest
from datetime import datetime, date
from tabernacleorm.fields import (
    Field,
    IntegerField,
    StringField,
    TextField,
    FloatField,
    BooleanField,
    DateTimeField,
    DateField,
    ForeignKey,
)

class TestIntegerField:
    def test_validate_integer(self):
        field = IntegerField()
        field.name = "test"
        assert field.validate(42) == 42
    
    def test_validate_string_to_integer(self):
        field = IntegerField()
        field.name = "test"
        assert field.validate("42") == 42
    
    def test_validate_none_nullable(self):
        field = IntegerField(nullable=True)
        field.name = "test"
        assert field.validate(None) is None
    
    def test_validate_none_not_nullable(self):
        field = IntegerField(nullable=False)
        field.name = "test"
        with pytest.raises(ValueError):
            field.validate(None)
    
    def test_field_attributes(self):
        field = IntegerField(primary_key=True, auto_increment=True)
        assert field.primary_key
        assert field.auto_increment
        assert field.get_schema()["type"] == "integer"

class TestStringField:
    def test_validate_string(self):
        field = StringField(max_length=100)
        field.name = "test"
        assert field.validate("hello") == "hello"
    
    def test_validate_max_length(self):
        field = StringField(max_length=5)
        field.name = "test"
        with pytest.raises(ValueError):
            field.validate("hello world")
            
    def test_field_attributes(self):
        field = StringField(max_length=255)
        assert field.max_length == 255
        assert field.get_schema()["type"] == "string"

class TestTextField:
    def test_validate_text(self):
        field = TextField()
        field.name = "test"
        long_text = "a" * 10000
        assert field.validate(long_text) == long_text

class TestFloatField:
    def test_validate_float(self):
        field = FloatField()
        field.name = "test"
        assert field.validate(3.14) == 3.14
    
    def test_validate_int_to_float(self):
        field = FloatField()
        field.name = "test"
        assert field.validate(42) == 42.0

class TestBooleanField:
    def test_validate_true(self):
        field = BooleanField()
        field.name = "test"
        assert field.validate(True) is True
    
    def test_validate_false(self):
        field = BooleanField()
        field.name = "test"
        assert field.validate(False) is False
    
    def test_default_value(self):
        field = BooleanField(default=True)
        assert field.default is True

class TestDateTimeField:
    def test_validate_datetime(self):
        field = DateTimeField()
        field.name = "test"
        now = datetime.now()
        assert field.validate(now) == now
    
    def test_validate_string(self):
        field = DateTimeField()
        field.name = "test"
        dt_str = "2024-01-15T10:30:00"
        result = field.validate(dt_str)
        assert isinstance(result, datetime)

class TestDateField:
    def test_validate_date(self):
        field = DateField()
        field.name = "test"
        today = date.today()
        assert field.validate(today) == today
    
    def test_validate_datetime_to_date(self):
        field = DateField()
        field.name = "test"
        now = datetime.now()
        result = field.validate(now)
        assert isinstance(result, date)

class TestForeignKey:
    def test_validate_integer(self):
        field = ForeignKey(to="users")
        field.name = "user_id"
        assert field.validate(1) == 1
