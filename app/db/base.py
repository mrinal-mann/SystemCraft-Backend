"""
SQLAlchemy Base Model Configuration

Provides the declarative base class with common configurations:
- Automatic table naming convention (snake_case from class name)
- Common columns (id, created_at, updated_at) as mixins
- Type annotations for modern SQLAlchemy 2.0 style

Design Decisions:
- Using SQLAlchemy 2.0 declarative style with mapped_column
- Timestamps use timezone-aware UTC
- ID is BigInteger for scalability
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import BigInteger, DateTime, MetaData
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
)

# Naming convention for constraints (important for Alembic migrations)
# This ensures consistent naming across all database objects
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    Features:
    - Automatic table name generation from class name
    - Consistent naming conventions for constraints
    - Type hints support via mapped_column
    """
    
    metadata = metadata
    
    # Common type annotations mapping
    type_annotation_map = {
        int: BigInteger,
    }


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamp columns.
    
    Usage:
        class User(Base, TimestampMixin):
            ...
    """
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TableNameMixin:
    """
    Mixin that generates table name from class name.
    Converts CamelCase to snake_case.
    
    Example: UserProfile -> user_profile
    """
    
    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        # Convert CamelCase to snake_case
        name = cls.__name__
        return "".join(
            ["_" + c.lower() if c.isupper() else c for c in name]
        ).lstrip("_")
