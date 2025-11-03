"""
Permission service for checking user access to servers.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserRole
from models.server import Server
from models.user_server_permission import UserServerPermission, ServerPermission


class PermissionService:
    """Service for managing and checking user permissions on servers."""

    @staticmethod
    async def has_server_permission(
        user: User,
        server_id: int,
        permission: ServerPermission,
        db: AsyncSession
    ) -> bool:
        """
        Check if a user has a specific permission on a server.

        Permission hierarchy:
        - ADMIN role: Has all permissions on all servers (bypass checks)
        - MODERATOR role: Has VIEW permission on all servers implicitly
        - VIEWER role: Only has explicitly granted permissions
        - MANAGE permission: Includes all other permissions

        Args:
            user: User to check
            server_id: Server ID
            permission: Permission to check
            db: Database session

        Returns:
            True if user has the permission, False otherwise
        """
        # ADMIN role bypasses all checks
        if user.role == UserRole.ADMIN:
            return True

        # MODERATOR has implicit VIEW permission on all servers
        if user.role == UserRole.MODERATOR and permission == ServerPermission.VIEW:
            return True

        # Check explicit permissions in database
        result = await db.execute(
            select(UserServerPermission).where(
                UserServerPermission.user_id == user.id,
                UserServerPermission.server_id == server_id
            )
        )
        permission_record = result.scalar_one_or_none()

        if not permission_record:
            return False

        return permission_record.has_permission(permission)

    @staticmethod
    async def get_user_server_permissions(
        user: User,
        server_id: int,
        db: AsyncSession
    ) -> List[str]:
        """
        Get all permissions a user has on a specific server.

        Args:
            user: User to check
            server_id: Server ID
            db: Database session

        Returns:
            List of permission strings
        """
        # ADMIN has all permissions
        if user.role == UserRole.ADMIN:
            return [p.value for p in ServerPermission]

        # Get explicit permissions
        result = await db.execute(
            select(UserServerPermission).where(
                UserServerPermission.user_id == user.id,
                UserServerPermission.server_id == server_id
            )
        )
        permission_record = result.scalar_one_or_none()

        if not permission_record:
            # MODERATOR has implicit VIEW
            if user.role == UserRole.MODERATOR:
                return [ServerPermission.VIEW.value]
            return []

        permissions = permission_record.permissions.copy()

        # Add implicit VIEW for MODERATOR if not already present
        if user.role == UserRole.MODERATOR and ServerPermission.VIEW.value not in permissions:
            permissions.append(ServerPermission.VIEW.value)

        return permissions

    @staticmethod
    async def get_accessible_servers(
        user: User,
        db: AsyncSession,
        permission: Optional[ServerPermission] = None
    ) -> List[int]:
        """
        Get list of server IDs the user can access.

        Args:
            user: User to check
            db: Database session
            permission: Optional specific permission to filter by

        Returns:
            List of server IDs the user can access
        """
        # ADMIN can access all servers
        if user.role == UserRole.ADMIN:
            result = await db.execute(select(Server.id))
            return [row[0] for row in result.all()]

        # Get servers with explicit permissions
        result = await db.execute(
            select(UserServerPermission.server_id).where(
                UserServerPermission.user_id == user.id
            )
        )
        server_ids = [row[0] for row in result.all()]

        # For MODERATOR with VIEW permission, return all servers
        if user.role == UserRole.MODERATOR and (permission is None or permission == ServerPermission.VIEW):
            result = await db.execute(select(Server.id))
            all_server_ids = [row[0] for row in result.all()]
            # Combine explicit permissions with all servers (for VIEW)
            return list(set(server_ids + all_server_ids))

        # Filter by specific permission if provided
        if permission:
            filtered_ids = []
            for server_id in server_ids:
                if await PermissionService.has_server_permission(user, server_id, permission, db):
                    filtered_ids.append(server_id)
            return filtered_ids

        return server_ids

    @staticmethod
    async def grant_permission(
        user_id: int,
        server_id: int,
        permissions: List[str],
        db: AsyncSession
    ) -> UserServerPermission:
        """
        Grant permissions to a user on a server.

        Args:
            user_id: User ID
            server_id: Server ID
            permissions: List of permission strings
            db: Database session

        Returns:
            UserServerPermission record
        """
        # Check if record already exists
        result = await db.execute(
            select(UserServerPermission).where(
                UserServerPermission.user_id == user_id,
                UserServerPermission.server_id == server_id
            )
        )
        permission_record = result.scalar_one_or_none()

        if permission_record:
            # Update existing permissions
            permission_record.permissions = permissions
        else:
            # Create new permission record
            permission_record = UserServerPermission(
                user_id=user_id,
                server_id=server_id,
                permissions=permissions
            )
            db.add(permission_record)

        await db.commit()
        await db.refresh(permission_record)
        return permission_record

    @staticmethod
    async def revoke_permission(
        user_id: int,
        server_id: int,
        db: AsyncSession
    ) -> bool:
        """
        Revoke all permissions from a user on a server.

        Args:
            user_id: User ID
            server_id: Server ID
            db: Database session

        Returns:
            True if permissions were revoked, False if no permissions existed
        """
        result = await db.execute(
            select(UserServerPermission).where(
                UserServerPermission.user_id == user_id,
                UserServerPermission.server_id == server_id
            )
        )
        permission_record = result.scalar_one_or_none()

        if permission_record:
            await db.delete(permission_record)
            await db.commit()
            return True

        return False
