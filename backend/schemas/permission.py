"""
Pydantic schemas for permissions.
"""

from typing import List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from models.user_server_permission import ServerPermission


class PermissionGrantRequest(BaseModel):
    """Request schema for granting permissions to a user on a server."""

    server_id: int = Field(..., description="Server ID")
    permissions: List[ServerPermission] = Field(
        ...,
        description="List of permissions to grant",
        min_length=1
    )


class PermissionResponse(BaseModel):
    """Response schema for user-server permissions."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    server_id: int
    permissions: List[str]
    created_at: datetime
    updated_at: datetime


class UserPermissionsResponse(BaseModel):
    """Response schema for all permissions of a user."""

    user_id: int
    permissions: List[PermissionResponse]


class ServerPermissionCheckResponse(BaseModel):
    """Response schema for checking if user has permission on a server."""

    user_id: int
    server_id: int
    permissions: List[str]
    effective_role: str
