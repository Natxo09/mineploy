"""
User model for authentication and authorization.
"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, Boolean, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import Base

if TYPE_CHECKING:
    from models.user_server_permission import UserServerPermission
    from models.refresh_token import RefreshToken


class UserRole(str, PyEnum):
    """User roles with different permission levels."""
    ADMIN = "admin"          # Full access
    MODERATOR = "moderator"  # Can manage servers, limited settings
    VIEWER = "viewer"        # Read-only access


class User(Base):
    """User model for authentication and permissions."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.VIEWER,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
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
    server_permissions: Mapped[list["UserServerPermission"]] = relationship(
        "UserServerPermission",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
