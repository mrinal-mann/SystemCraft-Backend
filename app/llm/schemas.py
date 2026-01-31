from typing import List, Optional
from pydantic import BaseModel, Field, validator


class LLMExplanation(BaseModel):
    """
    Schema for a single explanation from the LLM.
    
    The LLM explains WHY a missing component matters,
    not WHAT is missing (that's determined by rule-based analysis).
    """
    
    category: str = Field(
        ..., 
        description="Must match a valid SuggestionCategory: CACHING, SCALABILITY, SECURITY, RELIABILITY, PERFORMANCE, DATABASE, API_DESIGN, GENERAL"
    )
    
    why_it_matters: str = Field(
        ..., 
        min_length=10,
        max_length=500,
        description="Explain why this component is important in system design"
    )
    
    interview_angle: str = Field(
        ..., 
        min_length=10,
        max_length=500,
        description="How this topic might come up in a system design interview"
    )
    
    production_angle: str = Field(
        ..., 
        min_length=10,
        max_length=500,
        description="Real-world production implications of missing this component"
    )
    
    @validator('category')
    def validate_category(cls, v):
        """Ensure category matches our enum values."""
        valid_categories = [
            "CACHING", "SCALABILITY", "SECURITY", "RELIABILITY",
            "PERFORMANCE", "DATABASE", "API_DESIGN", "GENERAL"
        ]
        # Normalize to uppercase
        v_upper = v.upper()
        if v_upper not in valid_categories:
            raise ValueError(f"Invalid category: {v}. Must be one of {valid_categories}")
        return v_upper


class LLMResponse(BaseModel):
    """
    Root schema for LLM response.
    
    The LLM MUST return JSON matching this exact structure.
    Any deviation will cause validation to fail.
    """
    
    explanations: List[LLMExplanation] = Field(
        default_factory=list,
        description="List of explanations for missing components"
    )
    
    @classmethod
    def empty(cls) -> "LLMResponse":
        """Return an empty response (used as fallback)."""
        return cls(explanations=[])


class LLMRequestLog(BaseModel):
    """
    Schema for logging LLM requests (for debugging/auditing).
    """
    
    prompt: str
    response_raw: Optional[str] = None
    response_parsed: Optional[LLMResponse] = None
    error: Optional[str] = None
    model: str
    latency_ms: Optional[int] = None