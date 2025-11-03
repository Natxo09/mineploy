"""
User-Server permission mapping model.
"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, ForeignKey, DateTime, JSON, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import Base

if TYPE_CHECKING:
    from models.user import User
    from models.server import Server


class ServerPermission(str, PyEnum):
    """Individual server permissions."""
    VIEW = "view"                # Read-only access (status, logs, settings)
    CONSOLE = "console"          # Execute RCON commands
    START_STOP = "start_stop"    # Start, stop, restart server
    FILES = "files"              # File management (upload, download, edit)
    BACKUPS = "backups"          # Backup management (create, restore, delete)
    MANAGE = "manage"            # Full server control (settings, deletion, all above)


class UserServerPermission(Base):
    """
    Maps users to servers with specific permissions.

    This allows fine-grained control where a user can have different
    permissions on different servers, regardless of their global role.
    """

    __tablename__ = "user_server_permissions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    server_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("servers.id", ondelete="CASCADE"),
        nullable=False
    )

    # Store permissions as JSON array of permission strings
    # Example: ["view", "console", "start_stop"]
    permissions: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="server_permissions")
    server: Mapped["Server"] = relationship("Server", back_populates="user_permissions")

    # Ensure one user can only have one permission set per server
    __table_args__ = (
        UniqueConstraint('user_id', 'server_id', name='unique_user_server'),
    )

    def __repr__(self) -> str:
        return f"<UserServerPermission(user_id={self.user_id}, server_id={self.server_id}, permissions={self.permissions})>"

    def has_permission(self, permission: ServerPermission) -> bool:
        """Check if this permission set includes the given permission."""
        # MANAGE permission includes all others
        if ServerPermission.MANAGE.value in self.permissions:
            return True
        return permission.value in self.permissions

    def add_permission(self, permission: ServerPermission) -> None:
        """Add a permission to the set."""
        if permission.value not in self.permissions:
            self.permissions.append(permission.value)

    def remove_permission(self, permission: ServerPermission) -> None:
        """Remove a permission from the set."""
        if permission.value in self.permissions:
            self.permissions.remove(permission.value)
