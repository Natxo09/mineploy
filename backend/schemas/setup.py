"""
Pydantic schemas for setup wizard.
"""

from pydantic import BaseModel, EmailStr, Field


class SetupRequest(BaseModel):
    """Schema for initial setup request."""

    username: str = Field(..., min_length=3, max_length=50, description="Admin username")
    email: EmailStr = Field(..., description="Admin email address")
    password: str = Field(..., min_length=8, max_length=100, description="Admin password")


class SetupResponse(BaseModel):
    """Schema for setup completion response."""

    success: bool
    message: str
    admin_username: str
    next_steps: list[str]


class SetupStatus(BaseModel):
    """Schema for setup status check."""

    setup_completed: bool
    requires_setup: bool
    message: str
