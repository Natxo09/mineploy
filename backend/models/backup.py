"""
Backup model for server backups.
"""

from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Backup(Base):
    """Backup model for Minecraft server backups."""

    __tablename__ = "backups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("servers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)

    # Backup metadata
    is_automatic: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Backup(id={self.id}, server_id={self.server_id}, name={self.name})>"
