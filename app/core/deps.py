"""
Shared Dependencies

Contains reusable FastAPI dependencies, especially authentication.

Design Decisions:
- OAuth2 password bearer for token extraction from headers
- Single get_current_user dependency for protected routes
- Raises 401 for invalid/missing tokens
- Uses Prisma for database operations
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from prisma import Prisma

from app.core.config import settings
from app.core.database import get_db

# Token URL must match the login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(
    db: Prisma = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    Dependency to get the current authenticated user.
    
    Extracts user ID from JWT token and fetches user from database.
    Returns 401 if token is invalid or user doesn't exist.
    
    Usage:
        @router.get("/me")
        async def get_profile(current_user = Depends(get_current_user)):
            return current_user
    
    Note: Returns a Prisma User model (available after prisma generate).
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
    
    user = await db.user.find_unique(where={"id": int(user_id)})
    
    if user is None:
        raise credentials_exception
    
    return user
