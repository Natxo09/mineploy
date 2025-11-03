"""
API endpoints for system settings management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.dependencies import require_admin
from models.user import User
from models.system_settings import SystemSettings
from schemas.system_settings import SystemSettingsResponse, SystemSettingsUpdate

router = APIRouter()


async def get_or_create_settings(db: AsyncSession) -> SystemSettings:
    """
    Get system settings or create default if not exists.

    Args:
        db: Database session

    Returns:
        SystemSettings instance
    """
    result = await db.execute(select(SystemSettings))
    settings = result.scalar_one_or_none()

    if not settings:
        # Create default settings
        settings = SystemSettings(timezone="Europe/Madrid")
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings


@router.get("", response_model=SystemSettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
):
    """
    Get current system settings.

    No authentication required - settings are public.
    """
    settings = await get_or_create_settings(db)
    return settings


@router.put("", response_model=SystemSettingsResponse)
async def update_settings(
    settings_update: SystemSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Update system settings.

    Requires admin role.
    """
    settings = await get_or_create_settings(db)

    # Update fields
    settings.timezone = settings_update.timezone

    await db.commit()
    await db.refresh(settings)

    return settings
