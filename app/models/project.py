"""
Project Model

Represents a system design project created by a user.

Converted from Prisma schema:
- Uses SQLAlchemy 2.0 style with type annotations
- ProjectStatus as Python enum mapped to PostgreSQL
- Includes all relationships (owner, design_details, versions, suggestions)
"""

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.design import DesignDetails, DesignVersion
    from app.models.suggestion import Suggestion


class ProjectStatus(str, enum.Enum):
    """
    Project status enum.
    
    DRAFT: Initial state, project just created
    IN_PROGRESS: User is actively working on design
    ANALYZED: Design has been analyzed by the system
    """
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    ANALYZED = "ANALYZED"


class Project(Base):
    """
    Project model representing a system design project.
    
    Attributes:
        id: Primary key (auto-increment)
        title: Project title
        description: Optional project description
        status: Current project status (enum)
        owner_id: Foreign key to users table
        maturity_score: Design maturity score (0-100)
        maturity_reason: Explanation of maturity assessment
        created_at: Project creation timestamp
        updated_at: Last modification timestamp
    
    Relationships:
        owner: User who owns this project
        design_details: Current design content (one-to-one)
        design_versions: Historical versions (one-to-many)
        suggestions: Improvement suggestions (one-to-many)
    """
    
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus, name="project_status", create_constraint=True),
        default=ProjectStatus.DRAFT,
        nullable=False,
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Maturity Score (Step 3)
    maturity_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    maturity_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
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
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="projects",
        lazy="selectin",
    )
    
    design_details: Mapped[Optional["DesignDetails"]] = relationship(
        "DesignDetails",
        back_populates="project",
        uselist=False,  # One-to-one
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    design_versions: Mapped[List["DesignVersion"]] = relationship(
        "DesignVersion",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="DesignVersion.version_number.desc()",
        lazy="selectin",
    )
    
    suggestions: Mapped[List["Suggestion"]] = relationship(
        "Suggestion",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, title={self.title}, status={self.status})>"
