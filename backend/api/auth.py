"""
Authentication endpoints.
"""

from typing import Annotated
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.security import verify_password, create_access_token, get_password_hash, create_refresh_token
from core.dependencies import CurrentUser
from models.user import User
from models.refresh_token import RefreshToken
from schemas.user import UserLogin, TokenResponse, UserResponse, UserPasswordUpdate, RefreshTokenRequest


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Login endpoint - authenticate user and return JWT token.

    Args:
        credentials: Username and password
        db: Database session

    Returns:
        TokenResponse with access token and user info

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Find user by username
    result = await db.execute(
        select(User).where(User.username == credentials.username)
    )
    user = result.scalar_one_or_none()

    # Validate user exists and password is correct
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT access token
    access_token = create_access_token(data={"sub": str(user.id)})

    # Generate refresh token
    refresh_token_str = create_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expiration_days)

    # Store refresh token in database
    refresh_token_record = RefreshToken(
        token=refresh_token_str,
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(refresh_token_record)
    await db.commit()

    # Return tokens and user info
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/change-password")
async def change_password(
    password_data: UserPasswordUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Change the current user's password.

    Args:
        password_data: Current and new password
        current_user: Authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: 401 if current password is incorrect
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password"
        )

    # Hash and update new password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()

    return {"message": "Password updated successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser):
    """
    Get current authenticated user information.

    Args:
        current_user: Authenticated user

    Returns:
        UserResponse with current user info
    """
    return UserResponse.model_validate(current_user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Refresh access token using a refresh token.

    Args:
        refresh_request: Refresh token
        db: Database session

    Returns:
        New access token and refresh token

    Raises:
        HTTPException: 401 if refresh token is invalid, expired, or revoked
    """
    # Find refresh token in database
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == refresh_request.refresh_token)
    )
    refresh_token = result.scalar_one_or_none()

    # Validate refresh token
    if not refresh_token or not refresh_token.is_valid():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user
    result = await db.execute(
        select(User).where(User.id == refresh_token.user_id)
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Revoke old refresh token
    refresh_token.revoke()

    # Generate new tokens
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token_str = create_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expiration_days)

    # Store new refresh token
    new_refresh_token = RefreshToken(
        token=new_refresh_token_str,
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(new_refresh_token)
    await db.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token_str,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/logout")
async def logout(
    refresh_request: RefreshTokenRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Logout by revoking the refresh token.

    Args:
        refresh_request: Refresh token to revoke
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
    # Find and revoke refresh token
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == refresh_request.refresh_token,
            RefreshToken.user_id == current_user.id
        )
    )
    refresh_token = result.scalar_one_or_none()

    if refresh_token and not refresh_token.is_revoked:
        refresh_token.revoke()
        await db.commit()

    return {"message": "Successfully logged out"}
