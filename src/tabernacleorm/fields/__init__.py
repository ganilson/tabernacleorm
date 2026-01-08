"""
Field definitions for TabernacleORM models.
Now fully compatible with Pydantic.
"""

from typing import Any, Optional, Type, TYPE_CHECKING
from datetime import datetime, date
from pydantic import Field as PydanticField
from pydantic.fields import FieldInfo

class RelationshipInfo:
    """Metadata for relationships."""
    def __init__(self, back_populates: Optional[str] = None, link_model: Any = None, type: str = "OneToMany"):
        self.back_populates = back_populates
        self.link_model = link_model
        self.type = type  # OneToMany, ManyToOne, ManyToMany, OneToOne

def Field(
    default: Any = ...,
    *,
    primary_key: bool = False,
    nullable: bool = True,
    unique: bool = False,
    index: bool = False,
    max_length: Optional[int] = None,
    auto_increment: bool = False,
    auto_now: bool = False,
    auto_now_add: bool = False,
    foreign_key: Optional[str] = None,
    on_delete: str = "CASCADE",
    sa_type: Any = None, # SQLAlchemy type hint if needed later
    type: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Define a model field with ORM metadata.
    """
    json_schema_extra = kwargs.pop("json_schema_extra", {})
    tab_args = {
        "primary_key": primary_key,
        "nullable": nullable,
        "unique": unique,
        "index": index,
        "max_length": max_length,
        "auto_increment": auto_increment,
        "auto_now": auto_now,
        "auto_now_add": auto_now_add,
        "foreign_key": foreign_key,
        "on_delete": on_delete,
        "sa_type": sa_type
    }
    if type:
        tab_args["type"] = type
        
    if "tabernacle_args" in json_schema_extra:
        tab_args.update(json_schema_extra["tabernacle_args"])
        
    json_schema_extra["tabernacle_args"] = tab_args
    
    return PydanticField(default, json_schema_extra=json_schema_extra, **kwargs)

def Relationship(
    back_populates: Optional[str] = None,
    link_model: Any = None,
    type: str = "OneToMany",
    **kwargs
) -> Any:
    """
    Define a relationship to another model.
    """
    json_schema_extra = kwargs.pop("json_schema_extra", {})
    json_schema_extra.update({
        "relationship": RelationshipInfo(back_populates, link_model, type)
    })
    # Relationships are typically excluded from direct DB serialization
    return PydanticField(default=None, exclude=True, json_schema_extra=json_schema_extra, **kwargs)


# ----- Helpers / Aliases for backward compatibility & expressiveness -----

def IntegerField(
    primary_key: bool = False,
    auto_increment: bool = False,
    default: Any = ...,
    **kwargs
) -> Any:
    return Field(
        default=default,
        primary_key=primary_key,
        auto_increment=auto_increment,
        sa_type="INTEGER",
        type="integer",
        **kwargs
    )

def StringField(
    max_length: int = 255,
    default: Any = ...,
    **kwargs
) -> Any:
    return Field(
        default=default,
        max_length=max_length,
        sa_type="VARCHAR",
        type="string",
        **kwargs
    )

def TextField(default: Any = ..., **kwargs) -> Any:
    return Field(default=default, sa_type="TEXT", type="string", **kwargs)

def BooleanField(default: bool = False, **kwargs) -> Any:
    return Field(default=default, sa_type="BOOLEAN", type="boolean", **kwargs)

def FloatField(default: Any = ..., **kwargs) -> Any:
    return Field(default=default, sa_type="REAL", type="float", **kwargs)

def DateTimeField(
    auto_now: bool = False,
    auto_now_add: bool = False,
    default: Any = ...,
    **kwargs
) -> Any:
    return Field(
        default=default,
        auto_now=auto_now,
        auto_now_add=auto_now_add,
        sa_type="DATETIME",
        type="datetime",
        **kwargs
    )

def DateField(default: Any = ..., **kwargs) -> Any:
    return Field(default=default, sa_type="DATE", type="date", **kwargs)

def ForeignKey(
    to: str,
    on_delete: str = "CASCADE",
    **kwargs
) -> Any:
    """
    Foreign Key field.
    'to' should be 'TableName.field' or just 'TableName' (defaults to id).
    """
    return Field(
        foreign_key=to,
        on_delete=on_delete,
        sa_type="INTEGER", # Assuming integer FKs for now
        type="integer", 
        **kwargs
    )

def UUIDField(default: Any = ..., **kwargs) -> Any:
    return Field(default=default, sa_type="UUID", type="string", **kwargs)

def JSONField(default: Any = ..., **kwargs) -> Any:
    return Field(default=default, sa_type="JSON", type="json", **kwargs)

def ArrayField(default: Any = ..., **kwargs) -> Any:
    return Field(default=default, sa_type="ARRAY", type="array", **kwargs)

def EmbeddedField(model_class: Any, **kwargs) -> Any:
    """Field for embedded NoSQL documents."""
    return Field(sa_type="JSON", type="json", **kwargs) 

# Relationships
def OneToMany(to: str, back_populates: Optional[str] = None, **kwargs) -> Any:
    """One-to-Many relationship (virtual)."""
    return Relationship(back_populates=back_populates, link_model=to, type="OneToMany", **kwargs)

def ManyToMany(to: str, **kwargs) -> Any:
    """Many-to-Many relationship (virtual)."""
    return Relationship(link_model=to, type="ManyToMany", **kwargs)
