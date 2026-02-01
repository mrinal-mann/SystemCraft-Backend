"""
User Model

Represents registered users of the platform.

Converted from Prisma schema:
- Uses SQLAlchemy 2.0 style with type annotations
- Maintains same column names for database compatibility
- Includes relationship to projects
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project


class User(Base):
    """
    User model for authentication and project ownership.
    
    Attributes:
        id: Primary key (auto-increment)
        email: Unique email address
        hashed_password: Bcrypt hashed password
        full_name: Optional display name
        created_at: Account creation timestamp
        updated_at: Last modification timestamp
        projects: Related projects owned by user
    """
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
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
    
    # Relationships
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
