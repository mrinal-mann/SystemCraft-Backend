"""
Suggestion Schemas

Pydantic models for suggestion-related request/response validation.
"""

from datetime import datetime
from enum import Enum
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


class SuggestionBase(BaseModel):
    """Base schema for suggestions."""
    title: str = Field(..., max_length=255)
    description: str
    category: SuggestionCategory
    severity: SuggestionSeverity


class SuggestionCreate(SuggestionBase):
    """Schema for creating a suggestion (internal use by analysis service)."""
    design_version: int = 1


class SuggestionResponse(SuggestionBase):
    """Schema for suggestion in API responses."""
    id: int
    design_version: int
    project_id: int
    created_at: datetime

    class Config:
        from_attributes = True


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
class EnrichedSuggestionResponse(SuggestionResponse):
    """Schema for suggestions with LLM explanations."""
    why_it_matters: Optional[str] = None
    interview_angle: Optional[str] = None
    production_angle: Optional[str] = None
    llm_enriched: bool = False

    class Config:
        from_attributes = True