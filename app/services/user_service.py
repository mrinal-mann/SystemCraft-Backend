"""
User Service

Business logic for user operations using Prisma.

Design Decisions:
- Service layer separates business logic from HTTP layer
- All database operations go through service functions
- Async functions for Prisma compatibility
"""

from typing import Optional
from prisma import Prisma

from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


async def get_user_by_id(db: Prisma, user_id: int):
    """Get a user by their ID."""
    return await db.user.find_unique(where={"id": user_id})


async def get_user_by_email(db: Prisma, email: str):
    """Get a user by their email address."""
    return await db.user.find_unique(where={"email": email})


async def create_user(db: Prisma, user_data: UserCreate):
    """
    Create a new user.
    
    Args:
        db: Prisma client
        user_data: User creation data
    
    Returns:
        Created user object
    
    Note: Caller should check if email already exists before calling.
    """
    hashed_password = get_password_hash(user_data.password)
    
    user = await db.user.create(
        data={
            "email": user_data.email,
            "hashedPassword": hashed_password,
            "fullName": user_data.full_name,
        }
    )
    
    return user


async def authenticate_user(db: Prisma, email: str, password: str):
    """
    Authenticate a user by email and password.
    
    Returns:
        User object if authentication successful, None otherwise
    """
    user = await get_user_by_email(db, email)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashedPassword):
        return None
    
    return user


async def update_user(db: Prisma, user_id: int, user_data: UserUpdate):
    """
    Update user profile.
    
    Args:
        db: Prisma client
        user_id: User ID to update
        user_data: Update data (only provided fields are updated)
    
    Returns:
        Updated user object
    """
    update_dict = {}
    
    if user_data.full_name is not None:
        update_dict["fullName"] = user_data.full_name
    
    if user_data.password is not None:
        update_dict["hashedPassword"] = get_password_hash(user_data.password)
    
    user = await db.user.update(
        where={"id": user_id},
        data=update_dict
    )
    
    return user
