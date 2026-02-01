"""
Project Service

Business logic for project and design details operations using SQLAlchemy.

Design Decisions:
- Auto-creates DesignDetails when project is created (1:1 relationship)
- Design version increments on each update (for tracking analysis freshness)
- Async functions for SQLAlchemy async compatibility
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project, ProjectStatus
from app.models.design import DesignDetails
from app.schemas.project import ProjectCreate, ProjectUpdate, DesignDetailsUpdate


async def get_project_by_id(db: AsyncSession, project_id: int) -> Optional[Project]:
    """Get a project by ID with design details."""
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.design_details))
        .where(Project.id == project_id)
    )
    return result.scalar_one_or_none()


async def get_project_for_user(db: AsyncSession, project_id: int, user_id: int) -> Optional[Project]:
    """
    Get a project by ID, ensuring it belongs to the specified user.
    
    Returns None if project doesn't exist or doesn't belong to user.
    """
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.design_details))
        .where(Project.id == project_id, Project.owner_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_project_with_suggestions(db: AsyncSession, project_id: int, user_id: int) -> Optional[Project]:
    """
    Get a project with all related data including suggestions.
    """
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.design_details),
            selectinload(Project.suggestions)
        )
        .where(Project.id == project_id, Project.owner_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_projects(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[Project]:
    """
    Get all projects for a user with pagination.
    
    Args:
        db: AsyncSession
        user_id: Owner's user ID
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return
    
    Returns:
        List of projects ordered by updated_at descending
    """
    result = await db.execute(
        select(Project)
        .where(Project.owner_id == user_id)
        .order_by(Project.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def create_project(db: AsyncSession, project_data: ProjectCreate, owner_id: int) -> Project:
    """
    Create a new project with associated design details.
    
    Automatically creates a DesignDetails record for the project.
    """
    initial_content = project_data.design_content or ""
    
    # Create project
    project = Project(
        title=project_data.title,
        description=project_data.description,
        owner_id=owner_id,
        status=ProjectStatus.DRAFT,
    )
    
    db.add(project)
    await db.flush()  # Get the project.id
    
    # Create design details
    design_details = DesignDetails(
        project_id=project.id,
        content=initial_content,
        version=0,
    )
    
    db.add(design_details)
    await db.commit()
    
    # Refresh to get relationships
    await db.refresh(project)
    
    return project


async def update_project(db: AsyncSession, project_id: int, project_data: ProjectUpdate) -> Optional[Project]:
    """
    Update project metadata (title, description, status).
    
    Does NOT update design details - use update_design_details for that.
    """
    project = await get_project_by_id(db, project_id)
    if not project:
        return None
    
    if project_data.title is not None:
        project.title = project_data.title
    
    if project_data.description is not None:
        project.description = project_data.description
    
    if project_data.status is not None:
        project.status = ProjectStatus(project_data.status)
    
    await db.commit()
    await db.refresh(project)
    
    return project


async def update_design_details(db: AsyncSession, project_id: int, design_data: DesignDetailsUpdate) -> Optional[Project]:
    """
    Update the design details for a project.
    
    Versioning is now handled by the analysis service during the run_analysis 
    cycle to ensure versions correctly reflect analyzed "snapshots".
    """
    # Get or create design details
    result = await db.execute(
        select(DesignDetails).where(DesignDetails.project_id == project_id)
    )
    design_details = result.scalar_one_or_none()
    
    if design_details:
        design_details.content = design_data.content
    else:
        design_details = DesignDetails(
            project_id=project_id,
            content=design_data.content,
            version=0,
        )
        db.add(design_details)
    
    # Update project status to IN_PROGRESS
    project = await get_project_by_id(db, project_id)
    if project:
        project.status = ProjectStatus.IN_PROGRESS
    
    await db.commit()
    await db.refresh(project)
    
    return project


async def delete_project(db: AsyncSession, project_id: int) -> bool:
    """
    Delete a project and all associated data.
    
    Cascade delete will remove design_details and suggestions.
    Returns True on success.
    """
    project = await get_project_by_id(db, project_id)
    if not project:
        return False
    
    await db.delete(project)
    await db.commit()
    return True
