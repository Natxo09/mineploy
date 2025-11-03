"""
Pydantic schemas for system settings.
"""

from pydantic import BaseModel, Field
from datetime import datetime


class SystemSettingsBase(BaseModel):
    """Base schema for system settings."""
    timezone: str = Field(
        default="Europe/Madrid",
        description="System timezone (e.g., Europe/Madrid, America/New_York, Asia/Tokyo)"
    )


class SystemSettingsUpdate(SystemSettingsBase):
    """Schema for updating system settings."""
    pass


class SystemSettingsResponse(SystemSettingsBase):
    """Schema for system settings response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
