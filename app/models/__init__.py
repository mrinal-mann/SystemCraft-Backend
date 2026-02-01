"""
Models Package

Exports all SQLAlchemy models for easy importing.
"""

from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.design import DesignDetails, DesignVersion
from app.models.suggestion import (
    Suggestion,
    SuggestionCategory,
    SuggestionSeverity,
    SuggestionStatus,
)

__all__ = [
    # User
    "User",
    # Project
    "Project",
    "ProjectStatus",
    # Design
    "DesignDetails",
    "DesignVersion",
    # Suggestion
    "Suggestion",
    "SuggestionCategory",
    "SuggestionSeverity",
    "SuggestionStatus",
]
