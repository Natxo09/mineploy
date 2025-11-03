"""
Refresh Token model for JWT token renewal.
"""

from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import Base

if TYPE_CHECKING:
    from models.user import User


class RefreshToken(Base):
    """
    Refresh token for JWT authentication.

    Refresh tokens are long-lived tokens that can be used to obtain
    new access tokens without requiring the user to login again.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    token: Mapped[str] = mapped_column(String(500), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    revoked_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at}, is_revoked={self.is_revoked})>"

    def is_valid(self) -> bool:
        """Check if the refresh token is valid (not revoked and not expired)."""
        from datetime import timezone
        if self.is_revoked:
            return False
        if datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc if self.expires_at.tzinfo is None else self.expires_at.tzinfo):
            return False
        return True

    def revoke(self) -> None:
        """Revoke this refresh token."""
        from datetime import timezone
        self.is_revoked = True
        self.revoked_at = datetime.now(timezone.utc)
