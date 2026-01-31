"""
Analysis Endpoints

Handles triggering design analysis and retrieving suggestions.

Endpoints:
- POST /analysis/{project_id} - Trigger analysis on a project
- GET /analysis/{project_id}/suggestions - Get suggestions for a project
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from prisma import Prisma

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.suggestion import SuggestionResponse, AnalysisResponse
from app.services import project_service, analysis_service

router = APIRouter()


@router.post("/{project_id}", response_model=AnalysisResponse)
async def trigger_analysis(
    project_id: int,
    current_user = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """
    Trigger analysis on a project's design.
    
    This endpoint:
    1. Validates project ownership
    2. Clears any previous suggestions
    3. Runs rule-based analysis on the design content
    4. Saves generated suggestions
    5. Updates project status to ANALYZED
    
    **Note**: Analysis is synchronous for MVP. In production,
    this could be made asynchronous with background workers.
    
    Returns the generated suggestions.
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
    
    # Run analysis
    suggestions = await analysis_service.run_analysis(db, project_id)
    
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
            created_at=s.createdAt
        )
        for s in suggestions
    ]
    
    # Determine message based on results
    if len(suggestions) == 0:
        message = "Great job! Your design covers all major areas. No suggestions generated."
    elif len(suggestions) <= 3:
        message = f"Analysis complete. Found {len(suggestions)} areas for improvement."
    else:
        message = f"Analysis complete. Found {len(suggestions)} suggestions. Consider addressing critical items first."
    
    return AnalysisResponse(
        project_id=project_id,
        design_version=project.designDetails.version,
        suggestions_count=len(suggestions),
        suggestions=suggestion_responses,
        message=message
    )


@router.get("/{project_id}/suggestions", response_model=List[SuggestionResponse])
async def get_project_suggestions(
    project_id: int,
    current_user = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """
    Get all suggestions for a project.
    
    Returns suggestions from the most recent analysis.
    Run POST /analysis/{project_id} first to generate suggestions.
    """
    # Verify project belongs to user
    project = await project_service.get_project_for_user(db, project_id, current_user.id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    suggestions = await analysis_service.get_suggestions_for_project(db, project_id)
    
    return [
        SuggestionResponse(
            id=s.id,
            title=s.title,
            description=s.description,
            category=s.category,
            severity=s.severity,
            design_version=s.designVersion,
            project_id=s.projectId,
            created_at=s.createdAt
        )
        for s in suggestions
    ]
