"""
Shared Dependencies

Contains reusable FastAPI dependencies, especially authentication.

Design Decisions:
- OAuth2 password bearer for token extraction from headers
- Single get_current_user dependency for protected routes
- Raises 401 for invalid/missing tokens
- Uses SQLAlchemy async session for database operations
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

# Token URL must match the login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Extracts user ID from JWT token and fetches user from database.
    Returns 401 if token is invalid or user doesn't exist.
    
    Usage:
        @router.get("/me")
        async def get_profile(current_user: User = Depends(get_current_user)):
            return current_user
    
    Returns:
        User: The authenticated user's SQLAlchemy model instance.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # SQLAlchemy query to find user by ID
    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user
