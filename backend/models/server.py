"""
Minecraft Server model.
"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, Boolean, DateTime, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ServerType(str, PyEnum):
    """Minecraft server types."""
    VANILLA = "vanilla"
    PAPER = "paper"
    SPIGOT = "spigot"
    FABRIC = "fabric"
    FORGE = "forge"
    NEOFORGE = "neoforge"
    PURPUR = "purpur"


class ServerStatus(str, PyEnum):
    """Server status states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class Server(Base):
    """Minecraft server model."""

    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Server configuration
    server_type: Mapped[ServerType] = mapped_column(Enum(ServerType), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    port: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    rcon_port: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    rcon_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Resources
    memory_mb: Mapped[int] = mapped_column(Integer, default=2048)

    # Docker
    container_id: Mapped[str] = mapped_column(String(255), nullable=True)
    container_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Status
    status: Mapped[ServerStatus] = mapped_column(
        Enum(ServerStatus),
        default=ServerStatus.STOPPED,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    last_started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_stopped_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Server(id={self.id}, name={self.name}, status={self.status})>"
