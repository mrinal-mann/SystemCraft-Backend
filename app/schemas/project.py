"""
Project Schemas

Pydantic models for project-related request/response validation.

Design Decisions:
- DesignDetails embedded in Project responses (avoid extra API calls)
- Separate DesignDetailsUpdate for updating just the design content
- ProjectWithSuggestions for full project view including analysis results
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field

# Define enums locally for schemas to avoid dependency on generated models for validation
class ProjectStatus(str, Enum):
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    ANALYZED = "ANALYZED"

from app.schemas.suggestion import SuggestionResponse, DesignVersionResponse


# ============== Design Details Schemas ==============

class DesignDetailsBase(BaseModel):
    """Base schema for design details."""
    content: str = Field(default="", description="Free-form LLD content")


class DesignDetailsCreate(DesignDetailsBase):
    """Schema for creating design details (auto-created with project)."""
    pass


class DesignDetailsUpdate(BaseModel):
    """Schema for updating design details."""
    content: str = Field(..., description="Updated LLD content")


class DesignDetailsResponse(DesignDetailsBase):
    """Schema for design details in responses."""
    id: int
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Project Schemas ==============

class ProjectBase(BaseModel):
    """Base schema with common project fields."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    # Optional initial design content
    design_content: Optional[str] = Field(None, description="Initial LLD content")


class ProjectUpdate(BaseModel):
    """Schema for updating project (all fields optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[ProjectStatus] = None


class ProjectResponse(ProjectBase):
    """Schema for project in API responses."""
    id: int
    status: ProjectStatus
    owner_id: int
    created_at: datetime
    updated_at: datetime
    design_details: Optional[DesignDetailsResponse] = None
    # Step 3: Maturity Score
    maturity_score: int = 0
    maturity_reason: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Schema for listing projects (without full design details)."""
    id: int
    title: str
    description: Optional[str]
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    # Step 3: Maturity Score in list view
    maturity_score: int = 0

    class Config:
        from_attributes = True


class ProjectWithSuggestions(ProjectResponse):
    """Schema for project with analysis suggestions."""
    suggestions: List[SuggestionResponse] = []

    class Config:
        from_attributes = True


class ProjectWithEvolution(ProjectResponse):
    """Schema for project with version history (Step 4)."""
    suggestions: List[SuggestionResponse] = []
    design_versions: List[DesignVersionResponse] = []
    
    class Config:
        from_attributes = True

