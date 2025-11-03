"""
Permission management endpoints (admin only).
"""

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import AdminUser, CurrentUser
from models.user import User
from models.server import Server
from models.user_server_permission import UserServerPermission
from schemas.permission import (
    PermissionGrantRequest,
    PermissionResponse,
    UserPermissionsResponse,
    ServerPermissionCheckResponse
)
from services.permission_service import PermissionService


router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.post("/users/{user_id}", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def grant_permissions(
    user_id: int,
    permission_data: PermissionGrantRequest,
    admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Grant permissions to a user on a specific server (admin only).

    Args:
        user_id: User ID to grant permissions to
        permission_data: Server ID and permissions to grant
        admin: Admin user (from dependency)
        db: Database session

    Returns:
        Created/updated permission record

    Raises:
        HTTPException: 404 if user or server not found
    """
    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify server exists
    result = await db.execute(select(Server).where(Server.id == permission_data.server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )

    # Grant permissions
    permissions_list = [p.value for p in permission_data.permissions]
    permission_record = await PermissionService.grant_permission(
        user_id=user_id,
        server_id=permission_data.server_id,
        permissions=permissions_list,
        db=db
    )

    return PermissionResponse.model_validate(permission_record)


@router.get("/users/{user_id}", response_model=UserPermissionsResponse)
async def get_user_permissions(
    user_id: int,
    admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get all permissions for a specific user (admin only).

    Args:
        user_id: User ID
        admin: Admin user (from dependency)
        db: Database session

    Returns:
        List of all permissions the user has

    Raises:
        HTTPException: 404 if user not found
    """
    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get all permissions for user
    result = await db.execute(
        select(UserServerPermission).where(UserServerPermission.user_id == user_id)
    )
    permissions = result.scalars().all()

    return UserPermissionsResponse(
        user_id=user_id,
        permissions=[PermissionResponse.model_validate(p) for p in permissions]
    )


@router.get("/users/{user_id}/servers/{server_id}", response_model=ServerPermissionCheckResponse)
async def check_user_permission(
    user_id: int,
    server_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Check what permissions a user has on a specific server.
    Users can check their own permissions, admins can check anyone's.

    Args:
        user_id: User ID to check
        server_id: Server ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        User's permissions on the server

    Raises:
        HTTPException: 403 if trying to check other user's permissions without admin role
        HTTPException: 404 if user or server not found
    """
    # Only allow users to check their own permissions unless they're admin
    from models.user import UserRole
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only check your own permissions"
        )

    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify server exists
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )

    # Get permissions
    permissions = await PermissionService.get_user_server_permissions(user, server_id, db)

    return ServerPermissionCheckResponse(
        user_id=user_id,
        server_id=server_id,
        permissions=permissions,
        effective_role=user.role.value
    )


@router.delete("/users/{user_id}/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_permissions(
    user_id: int,
    server_id: int,
    admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Revoke all permissions from a user on a specific server (admin only).

    Args:
        user_id: User ID
        server_id: Server ID
        admin: Admin user (from dependency)
        db: Database session

    Raises:
        HTTPException: 404 if no permissions found
    """
    # Revoke permissions
    revoked = await PermissionService.revoke_permission(user_id, server_id, db)

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No permissions found for this user on this server"
        )
