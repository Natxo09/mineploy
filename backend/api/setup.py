"""
Setup wizard endpoint for initial configuration.
Creates the first admin user.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.security import get_password_hash
from models.user import User, UserRole
from schemas.setup import SetupRequest, SetupResponse, SetupStatus

router = APIRouter()


@router.get(
    "/status",
    response_model=SetupStatus,
    summary="Check setup status",
    description="Check if initial setup has been completed",
)
async def get_setup_status(db: AsyncSession = Depends(get_db)) -> SetupStatus:
    """
    Check if the application requires initial setup.

    Returns:
        SetupStatus: Current setup status
    """
    # Check if any users exist
    result = await db.execute(select(User).limit(1))
    user_exists = result.scalar_one_or_none() is not None

    if user_exists:
        return SetupStatus(
            setup_completed=True,
            requires_setup=False,
            message="Setup has already been completed",
        )

    return SetupStatus(
        setup_completed=False,
        requires_setup=True,
        message="Initial setup required. Please create an admin user.",
    )


@router.post(
    "/initialize",
    response_model=SetupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize application",
    description="Create the first admin user and complete initial setup",
)
async def initialize_setup(
    setup_data: SetupRequest, db: AsyncSession = Depends(get_db)
) -> SetupResponse:
    """
    Initialize the application by creating the first admin user.

    This endpoint can only be used once. After the first admin user is created,
    subsequent calls will be rejected.

    Args:
        setup_data: Setup configuration with admin credentials
        db: Database session

    Returns:
        SetupResponse: Setup completion information

    Raises:
        HTTPException: If setup has already been completed
    """
    # Check if setup has already been completed
    result = await db.execute(select(User).limit(1))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Setup has already been completed. Cannot create another admin user through this endpoint.",
        )

    # Check if username already exists (shouldn't happen, but extra safety)
    result = await db.execute(select(User).where(User.username == setup_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == setup_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    # Create the first admin user
    admin_user = User(
        username=setup_data.username,
        email=setup_data.email,
        hashed_password=get_password_hash(setup_data.password),
        role=UserRole.ADMIN,
        is_active=True,
    )

    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)

    return SetupResponse(
        success=True,
        message="Initial setup completed successfully",
        admin_username=admin_user.username,
        next_steps=[
            "Log in with your admin credentials",
            "Configure your first Minecraft server",
            "Set up backups (optional)",
            "Invite additional users (optional)",
        ],
    )
