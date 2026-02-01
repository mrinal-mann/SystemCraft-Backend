"""
Authentication Endpoints

Handles user registration, login, and profile management.

Endpoints:
- POST /auth/signup - Register new user
- POST /auth/login - Login and get JWT token
- GET /auth/me - Get current user profile
- PUT /auth/me - Update current user profile
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
    Token,
)
from app.services import user_service

router = APIRouter()

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.
    
    - **email**: Valid email address (will be used for login)
    - **password**: Minimum 6 characters
    - **full_name**: Optional display name
    """
    # Check if email already exists
    existing_user = await user_service.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = await user_service.create_user(db, user_data)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Login with email and password to get access token.
    
    Uses OAuth2 password flow - send credentials as form data:
    - **username**: Email address
    - **password**: User password
    
    Returns JWT access token for authenticated requests.
    """
    user = await user_service.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create JWT token with user ID as subject
    access_token = create_access_token(subject=user.id)
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's profile.
    
    Requires valid JWT token in Authorization header.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the current authenticated user's profile.
    
    Only provided fields will be updated.
    - **full_name**: Update display name
    - **password**: Update password (minimum 6 characters)
    """
    updated_user = await user_service.update_user(db, current_user.id, user_data)
    return UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        full_name=updated_user.full_name,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at
    )
