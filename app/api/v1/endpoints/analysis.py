"""
Analysis Endpoints

Handles triggering design analysis and retrieving suggestions.

Endpoints (in order of matching priority):
- PATCH /analysis/suggestions/{suggestion_id}/status - Update suggestion status (FIRST - static path)
- POST /analysis/{project_id} - Trigger analysis on a project
- GET /analysis/{project_id}/suggestions - Get suggestions for a project
- GET /analysis/{project_id}/evolution - Get project evolution history
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from prisma import Prisma

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.suggestion import (
    SuggestionResponse, 
    AnalysisResponse, 
    SuggestionStatusUpdate,
    SuggestionStatus,
    DesignVersionResponse,
    ProjectEvolutionResponse
)
from app.services import project_service, analysis_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ============== STATIC ROUTES FIRST (before dynamic {project_id} routes) ==============

@router.patch("/suggestions/{suggestion_id}/status", response_model=SuggestionResponse)
async def update_suggestion_status(
    suggestion_id: int,
    status_update: SuggestionStatusUpdate,
    current_user = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """
    Manually update a suggestion's status.
    
    Use this to:
    - Mark a suggestion as IGNORED if not applicable
    - Manually mark as ADDRESSED
    - Reopen a closed suggestion
    """
    logger.info(f"[STATUS UPDATE] Updating suggestion {suggestion_id} to {status_update.status}")
    
    # First get the suggestion to verify ownership
    suggestion = await db.suggestion.find_unique(
        where={"id": suggestion_id},
        include={"project": True}
    )
    
    if not suggestion:
        logger.warning(f"[STATUS UPDATE] Suggestion {suggestion_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suggestion not found"
        )
    
    if suggestion.project.ownerId != current_user.id:
        logger.warning(f"[STATUS UPDATE] User {current_user.id} not authorized for suggestion {suggestion_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this suggestion"
        )
    
    # Update the status
    updated = await analysis_service.update_suggestion_status(
        db, 
        suggestion_id, 
        status_update.status.value
    )
    
    logger.info(f"[STATUS UPDATE] Success! Suggestion {suggestion_id} is now {updated.status}")
    
    return SuggestionResponse(
        id=updated.id,
        title=updated.title,
        description=updated.description,
        category=updated.category,
        severity=updated.severity,
        design_version=updated.designVersion,
        project_id=updated.projectId,
        created_at=updated.createdAt,
        status=updated.status,
        addressed_at=updated.addressedAt,
        addressed_in_version=updated.addressedInVersion
    )


# ============== DYNAMIC ROUTES (with {project_id}) ==============

@router.post("/{project_id}", response_model=AnalysisResponse)
async def trigger_analysis(
    project_id: int,
    current_user = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """
    Trigger analysis on a project's design.
    
    This endpoint (ENHANCED):
    1. Validates project ownership
    2. Checks if previous suggestions are now addressed (auto-detection)
    3. Runs rule-based analysis for new suggestions
    4. Calculates maturity score (0-5)
    5. Creates design version snapshot for history
    6. Updates project status and maturity
    
    **New Features:**
    - Auto-marks suggestions as ADDRESSED when keywords appear
    - Calculates maturity score based on concept coverage
    - Creates version history for tracking progress
    
    Returns enhanced analysis results with maturity and addressed count.
    """
    # Verify project belongs to user
    project = await project_service.get_project_for_user(db, project_id, current_user.id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if design details exist
    if not project.designDetails or not project.designDetails.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has no design content to analyze. Add design details first."
        )
    
    # Run analysis (now returns dict with enhanced data)
    result = await analysis_service.run_analysis(db, project_id)
    
    # Convert to response format
    suggestion_responses = [
        SuggestionResponse(
            id=s.id,
            title=s.title,
            description=s.description,
            category=s.category,
            severity=s.severity,
            design_version=s.designVersion,
            project_id=s.projectId,
            created_at=s.createdAt,
            status=s.status,
            addressed_at=s.addressedAt,
            addressed_in_version=s.addressedInVersion
        )
        for s in result["suggestions"]
    ]
    
    # Build intelligent message
    addressed = result["newly_addressed_count"]
    new_count = result.get("new_suggestions_count", 0)
    open_count = len([s for s in result["suggestions"] if s.status == "OPEN"])
    maturity = result["maturity_score"]
    
    message_parts = []
    if addressed > 0:
        message_parts.append(f"🎉 {addressed} suggestion(s) addressed!")
    if new_count > 0:
        message_parts.append(f"Found {new_count} new area(s) for improvement.")
    if open_count == 0:
        message_parts.append("All suggestions addressed!")
    elif maturity == 5:
        message_parts.append(f"Comprehensive design (maturity: {maturity}/5)!")
    else:
        message_parts.append(f"Maturity: {maturity}/5. Keep improving!")
    
    message = " ".join(message_parts) if message_parts else "Analysis complete."
    
    return AnalysisResponse(
        project_id=project_id,
        design_version=result["design_version"],
        suggestions_count=len(result["suggestions"]),
        suggestions=suggestion_responses,
        message=message,
        maturity_score=result["maturity_score"],
        maturity_reason=result["maturity_reason"],
        newly_addressed_count=result["newly_addressed_count"]
    )


@router.get("/{project_id}/suggestions", response_model=List[SuggestionResponse])
async def get_project_suggestions(
    project_id: int,
    status_filter: str = None,
    current_user = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """
    Get all suggestions for a project.
    
    Optional filter by status: OPEN, ADDRESSED, IGNORED
    Returns suggestions from all analyses.
    """
    # Verify project belongs to user
    project = await project_service.get_project_for_user(db, project_id, current_user.id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    suggestions = await analysis_service.get_suggestions_for_project(db, project_id)
    
    # Filter by status if provided
    if status_filter:
        suggestions = [s for s in suggestions if s.status == status_filter.upper()]
    
    return [
        SuggestionResponse(
            id=s.id,
            title=s.title,
            description=s.description,
            category=s.category,
            severity=s.severity,
            design_version=s.designVersion,
            project_id=s.projectId,
            created_at=s.createdAt,
            status=s.status,
            addressed_at=s.addressedAt,
            addressed_in_version=s.addressedInVersion
        )
        for s in suggestions
    ]


@router.get("/{project_id}/evolution", response_model=ProjectEvolutionResponse)
async def get_project_evolution(
    project_id: int,
    current_user = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """
    Get the evolution history of a project.
    
    Shows:
    - All design versions with timestamps
    - Maturity score at each version
    - Number of open suggestions at each version
    - Progress summary
    
    Use this to visualize improvement over time.
    """
    # Verify project belongs to user
    project = await project_service.get_project_for_user(db, project_id, current_user.id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    evolution = await analysis_service.get_project_evolution(db, project_id)
    
    if not evolution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No evolution data found"
        )
    
    # Convert versions to response format
    version_responses = [
        DesignVersionResponse(
            id=v.id,
            version_number=v.versionNumber,
            content=v.content,
            created_at=v.createdAt,
            maturity_score=v.maturityScore,
            suggestions_count=v.suggestionsCount
        )
        for v in evolution["versions"]
    ]
    
    return ProjectEvolutionResponse(
        project_id=evolution["project_id"],
        current_version=evolution["current_version"],
        current_maturity_score=evolution["current_maturity_score"],
        versions=version_responses,
        progress_summary=evolution["progress_summary"]
    )


