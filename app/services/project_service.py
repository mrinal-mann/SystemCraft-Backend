"""
Project Service

Business logic for project and design details operations using Prisma.

Design Decisions:
- Auto-creates DesignDetails when project is created (1:1 relationship)
- Design version increments on each update (for tracking analysis freshness)
- Async functions for Prisma compatibility
"""

from typing import List
from prisma import Prisma

from app.schemas.project import ProjectCreate, ProjectUpdate, DesignDetailsUpdate


async def get_project_by_id(db: Prisma, project_id: int):
    """Get a project by ID with design details."""
    return await db.project.find_unique(
        where={"id": project_id},
        include={"designDetails": True}
    )


async def get_project_for_user(db: Prisma, project_id: int, user_id: int):
    """
    Get a project by ID, ensuring it belongs to the specified user.
    
    Returns None if project doesn't exist or doesn't belong to user.
    """
    return await db.project.find_first(
        where={
            "id": project_id,
            "ownerId": user_id
        },
        include={"designDetails": True}
    )


async def get_project_with_suggestions(db: Prisma, project_id: int, user_id: int):
    """
    Get a project with all related data including suggestions.
    """
    return await db.project.find_first(
        where={
            "id": project_id,
            "ownerId": user_id
        },
        include={
            "designDetails": True,
            "suggestions": {
                "order_by": {"createdAt": "desc"}
            }
        }
    )


async def get_user_projects(db: Prisma, user_id: int, skip: int = 0, limit: int = 100) -> List:
    """
    Get all projects for a user with pagination.
    
    Args:
        db: Prisma client
        user_id: Owner's user ID
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return
    
    Returns:
        List of projects ordered by updated_at descending
    """
    return await db.project.find_many(
        where={"ownerId": user_id},
        order={"updatedAt": "desc"},
        skip=skip,
        take=limit
    )


async def create_project(db: Prisma, project_data: ProjectCreate, owner_id: int):
    """
    Create a new project with associated design details.
    
    Automatically creates a DesignDetails record for the project.
    """
    initial_content = project_data.design_content or ""
    
    # Create project with nested design details in single transaction
    project = await db.project.create(
        data={
            "title": project_data.title,
            "description": project_data.description,
            "ownerId": owner_id,
            "status": "DRAFT",
            "designDetails": {
                "create": {
                    "content": initial_content,
                    "version": 0
                }
            }
        },
        include={"designDetails": True}
    )
    
    return project


async def update_project(db: Prisma, project_id: int, project_data: ProjectUpdate):
    """
    Update project metadata (title, description, status).
    
    Does NOT update design details - use update_design_details for that.
    """
    update_dict = {}
    
    if project_data.title is not None:
        update_dict["title"] = project_data.title
    
    if project_data.description is not None:
        update_dict["description"] = project_data.description
    
    if project_data.status is not None:
        update_dict["status"] = project_data.status
    
    project = await db.project.update(
        where={"id": project_id},
        data=update_dict,
        include={"designDetails": True}
    )
    
    return project


async def update_design_details(db: Prisma, project_id: int, design_data: DesignDetailsUpdate):
    """
    Update the design details for a project.
    
    Versioning is now handled by the analysis service during the run_analysis 
    cycle to ensure versions correctly reflect analyzed "snapshots".
    """
    # Simply update design content
    await db.designdetails.upsert(
        where={"projectId": project_id},
        data={
            "create": {
                "projectId": project_id,
                "content": design_data.content,
                "version": 0
            },
            "update": {
                "content": design_data.content
            }
        }
    )
    
    # Update project status to IN_PROGRESS
    project = await db.project.update(
        where={"id": project_id},
        data={"status": "IN_PROGRESS"},
        include={"designDetails": True}
    )
    
    return project


async def delete_project(db: Prisma, project_id: int) -> bool:
    """
    Delete a project and all associated data.
    
    Cascade delete will remove design_details and suggestions.
    Returns True on success.
    """
    await db.project.delete(where={"id": project_id})
    return True
