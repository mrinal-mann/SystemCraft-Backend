"""
Project Endpoints

Handles project CRUD and design details management.

Endpoints:
- GET /projects - List user's projects
- POST /projects - Create new project
- GET /projects/{id} - Get project details
- PUT /projects/{id} - Update project metadata
- DELETE /projects/{id} - Delete project
- PUT /projects/{id}/design - Update design details
- GET /projects/{id}/full - Get project with suggestions
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.suggestion import Suggestion
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectWithSuggestions,
    DesignDetailsUpdate,
    DesignDetailsResponse,
)
from app.schemas.suggestion import SuggestionResponse
from app.services import project_service

router = APIRouter()


def project_to_response(project: Project) -> ProjectResponse:
    """Convert SQLAlchemy project to response schema."""
    design_details = None
    if project.design_details:
        design_details = DesignDetailsResponse(
            id=project.design_details.id,
            content=project.design_details.content,
            version=project.design_details.version,
            created_at=project.design_details.created_at,
            updated_at=project.design_details.updated_at
        )
    
    return ProjectResponse(
        id=project.id,
        title=project.title,
        description=project.description,
        status=project.status.value,
        owner_id=project.owner_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        design_details=design_details,
        maturity_score=project.maturity_score,
        maturity_reason=project.maturity_reason
    )


def project_to_list_response(project: Project) -> ProjectListResponse:
    """Convert SQLAlchemy project to list response schema."""
    return ProjectListResponse(
        id=project.id,
        title=project.title,
        description=project.description,
        status=project.status.value,
        created_at=project.created_at,
        updated_at=project.updated_at,
        maturity_score=project.maturity_score
    )


@router.get("", response_model=List[ProjectListResponse])
async def list_projects(
    skip: int = Query(0, ge=0, description="Number of projects to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum projects to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all projects for the current user.
    
    Returns projects ordered by last updated (newest first).
    Supports pagination with skip and limit parameters.
    """
    projects = await project_service.get_user_projects(db, current_user.id, skip=skip, limit=limit)
    return [project_to_list_response(p) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new system design project.
    
    - **title**: Project name (required)
    - **description**: Brief project description
    - **design_content**: Optional initial LLD content
    
    Automatically creates associated design details.
    """
    project = await project_service.create_project(db, project_data, current_user.id)
    return project_to_response(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific project by ID.
    
    Returns project with design details (but not suggestions).
    """
    project = await project_service.get_project_for_user(db, project_id, current_user.id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project_to_response(project)


@router.get("/{project_id}/full", response_model=ProjectWithSuggestions)
async def get_project_with_suggestions(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a project with all analysis suggestions.
    
    Use this endpoint after running analysis to see all suggestions.
    """
    project = await project_service.get_project_with_suggestions(db, project_id, current_user.id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Convert to response
    design_details = None
    if project.design_details:
        design_details = DesignDetailsResponse(
            id=project.design_details.id,
            content=project.design_details.content,
            version=project.design_details.version,
            created_at=project.design_details.created_at,
            updated_at=project.design_details.updated_at
        )
    
    suggestions = []
    if project.suggestions:
        suggestions = [
            SuggestionResponse(
                id=s.id,
                title=s.title,
                description=s.description,
                category=s.category.value,
                severity=s.severity.value,
                design_version=s.design_version,
                project_id=s.project_id,
                created_at=s.created_at,
                status=s.status.value,
                addressed_at=s.addressed_at,
                addressed_in_version=s.addressed_in_version
            )
            for s in project.suggestions
        ]
    
    return ProjectWithSuggestions(
        id=project.id,
        title=project.title,
        description=project.description,
        status=project.status.value,
        owner_id=project.owner_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        design_details=design_details,
        suggestions=suggestions,
        maturity_score=project.maturity_score,
        maturity_reason=project.maturity_reason
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update project metadata (title, description, status).
    
    Use PUT /projects/{id}/design to update design content.
    """
    project = await project_service.get_project_for_user(db, project_id, current_user.id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    updated_project = await project_service.update_project(db, project_id, project_data)
    return project_to_response(updated_project)


@router.put("/{project_id}/design", response_model=ProjectResponse)
async def update_design_details(
    project_id: int,
    design_data: DesignDetailsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the design details (LLD content) for a project.
    
    - **content**: The full LLD text content
    
    Increments design version and sets project status to IN_PROGRESS.
    After updating, run analysis to get new suggestions.
    """
    project = await project_service.get_project_for_user(db, project_id, current_user.id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    updated_project = await project_service.update_design_details(db, project_id, design_data)
    return project_to_response(updated_project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a project and all associated data.
    
    This action cannot be undone. All design details and suggestions
    will be permanently removed.
    """
    project = await project_service.get_project_for_user(db, project_id, current_user.id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    await project_service.delete_project(db, project_id)
    return None
