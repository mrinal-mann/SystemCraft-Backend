"""
User Service

Business logic for user operations using SQLAlchemy.

Design Decisions:
- Service layer separates business logic from HTTP layer
- All database operations go through service functions
- Async functions for SQLAlchemy async compatibility
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get a user by their ID."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get a user by their email address."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Create a new user.
    
    Args:
        db: AsyncSession
        user_data: User creation data
    
    Returns:
        Created user object
    
    Note: Caller should check if email already exists before calling.
    """
    hashed_password = get_password_hash(user_data.password)
    
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.
    
    Returns:
        User object if authentication successful, None otherwise
    """
    user = await get_user_by_email(db, email)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


async def update_user(db: AsyncSession, user_id: int, user_data: UserUpdate) -> Optional[User]:
    """
    Update user profile.
    
    Args:
        db: AsyncSession
        user_id: User ID to update
        user_data: Update data (only provided fields are updated)
    
    Returns:
        Updated user object
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    
    if user_data.password is not None:
        user.hashed_password = get_password_hash(user_data.password)
    
    await db.commit()
    await db.refresh(user)
    
    return user
