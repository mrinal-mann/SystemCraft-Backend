"""
Suggestion Schemas

Pydantic models for suggestion-related request/response validation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class SuggestionCategory(str, Enum):
    CACHING = "CACHING"
    SCALABILITY = "SCALABILITY"
    SECURITY = "SECURITY"
    RELIABILITY = "RELIABILITY"
    PERFORMANCE = "PERFORMANCE"
    DATABASE = "DATABASE"
    API_DESIGN = "API_DESIGN"
    GENERAL = "GENERAL"


class SuggestionSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


# Step 2: Suggestion Status
class SuggestionStatus(str, Enum):
    OPEN = "OPEN"
    ADDRESSED = "ADDRESSED"
    IGNORED = "IGNORED"


class SuggestionBase(BaseModel):
    """Base schema for suggestions."""
    title: str = Field(..., max_length=255)
    description: str
    category: SuggestionCategory
    severity: SuggestionSeverity


class SuggestionCreate(SuggestionBase):
    """Schema for creating a suggestion (internal use by analysis service)."""
    design_version: int = 1
    trigger_keywords: List[str] = []


class SuggestionResponse(SuggestionBase):
    """Schema for suggestion in API responses."""
    id: int
    design_version: int
    project_id: int
    created_at: datetime
    status: SuggestionStatus = SuggestionStatus.OPEN
    addressed_at: Optional[datetime] = None
    addressed_in_version: Optional[int] = None

    class Config:
        from_attributes = True


class SuggestionStatusUpdate(BaseModel):
    """Schema for manually updating suggestion status."""
    status: SuggestionStatus


class AnalysisRequest(BaseModel):
    """Schema for triggering analysis on a project."""
    # Currently empty - just triggers analysis on existing design
    # Could add options like: analysis_depth, focus_areas, etc.
    pass


class AnalysisResponse(BaseModel):
    """Schema for analysis results."""
    project_id: int
    design_version: int
    suggestions_count: int
    suggestions: list[SuggestionResponse]
    message: str
    # Step 3: Maturity Score
    maturity_score: int = 0
    maturity_reason: Optional[str] = None
    # Step 2: Addressed suggestions count
    newly_addressed_count: int = 0


class EnrichedSuggestionResponse(SuggestionResponse):
    """Schema for suggestions with LLM explanations."""
    why_it_matters: Optional[str] = None
    interview_angle: Optional[str] = None
    production_angle: Optional[str] = None
    llm_enriched: bool = False

    class Config:
        from_attributes = True


# Step 4: Design Version History Schema
class DesignVersionResponse(BaseModel):
    """Schema for design version history."""
    id: int
    version_number: int
    content: str
    created_at: datetime
    maturity_score: int
    suggestions_count: int

    class Config:
        from_attributes = True


class ProjectEvolutionResponse(BaseModel):
    """Schema for showing project evolution over time."""
    project_id: int
    current_version: int
    current_maturity_score: int
    versions: List[DesignVersionResponse]
    progress_summary: str
