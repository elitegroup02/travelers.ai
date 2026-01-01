"""Authentication router with user registration, login, and token management."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import (
    TokenPair,
    create_token_pair,
    get_password_hash,
    verify_password,
    verify_refresh_token,
)
from ..dependencies.auth import CurrentUser
from ..models.user import User

router = APIRouter(prefix="/auth")


# Request/Response schemas
class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    display_name: str | None = Field(None, max_length=100)
    preferred_language: str = Field(default="en", pattern="^(en|es)$")


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class UserResponse(BaseModel):
    """User info response."""

    id: str
    email: str
    display_name: str | None
    preferred_language: str

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Authentication response with tokens and user info."""

    user: UserResponse
    tokens: TokenPair


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Create a new user account.

    Returns the new user info and authentication tokens.
    """
    # Check if email already exists
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    user = User(
        email=request.email,
        hashed_password=get_password_hash(request.password),
        display_name=request.display_name,
        preferred_language=request.preferred_language,
        preferences={},
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate tokens
    tokens = create_token_pair(str(user.id))

    return AuthResponse(
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            preferred_language=user.preferred_language,
        ),
        tokens=tokens,
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Login and get access/refresh tokens.

    Returns user info and authentication tokens.
    """
    # Find user by email
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Generate tokens
    tokens = create_token_pair(str(user.id))

    return AuthResponse(
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            preferred_language=user.preferred_language,
        ),
        tokens=tokens,
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(
    request: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenPair:
    """Refresh access token using a refresh token.

    Returns a new token pair.
    """
    # Verify refresh token
    user_id = verify_refresh_token(request.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Verify user still exists
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Generate new tokens
    return create_token_pair(str(user.id))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    """Get current authenticated user info."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        display_name=current_user.display_name,
        preferred_language=current_user.preferred_language,
    )


@router.patch("/me", response_model=UserResponse)
async def update_me(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    display_name: str | None = None,
    preferred_language: str | None = None,
) -> UserResponse:
    """Update current user's profile."""
    if display_name is not None:
        current_user.display_name = display_name
    if preferred_language is not None:
        if preferred_language not in ("en", "es"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Language must be 'en' or 'es'",
            )
        current_user.preferred_language = preferred_language

    await db.commit()
    await db.refresh(current_user)

    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        display_name=current_user.display_name,
        preferred_language=current_user.preferred_language,
    )
