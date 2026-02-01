"""
Design Models

Contains models for design content:
- DesignDetails: Current design content (one-to-one with Project)
- DesignVersion: Historical snapshots for version tracking

Converted from Prisma schema with SQLAlchemy 2.0 style.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    Text,
    Integer,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project


class DesignDetails(Base):
    """
    Current design content for a project.
    
    One-to-one relationship with Project.
    Stores the current/latest design document content.
    
    Attributes:
        id: Primary key
        content: The actual design document content (markdown/text)
        version: Current version number
        project_id: Foreign key to project (unique for 1:1)
        created_at: Creation timestamp
        updated_at: Last modification timestamp
    """
    
    __tablename__ = "design_details"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        unique=True,  # Enforces one-to-one relationship
        nullable=False,
        index=True,
    )
    
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
    
    # Relationship
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="design_details",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<DesignDetails(id={self.id}, project_id={self.project_id}, version={self.version})>"


class DesignVersion(Base):
    """
    Historical snapshot of design content.
    
    Every edit can create a new version for tracking progress over time.
    Stores a snapshot of maturity score and suggestions count at that version.
    
    Attributes:
        id: Primary key
        version_number: Incrementing version number per project
        content: Design content at this version
        project_id: Foreign key to project
        maturity_score: Maturity score at this version
        suggestions_count: Number of suggestions at this version
        created_at: When this version was created
    """
    
    __tablename__ = "design_versions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Snapshot of maturity at this version
    maturity_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    suggestions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    # Relationship
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="design_versions",
        lazy="selectin",
    )
    
    # Unique constraint on project_id + version_number
    __table_args__ = (
        UniqueConstraint("project_id", "version_number", name="uq_design_versions_project_version"),
    )
    
    def __repr__(self) -> str:
        return f"<DesignVersion(id={self.id}, project_id={self.project_id}, version={self.version_number})>"
