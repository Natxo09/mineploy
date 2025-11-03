"""
Pydantic schemas for Minecraft servers.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional
from models.server import ServerType, ServerStatus


class ServerBase(BaseModel):
    """Base server schema with common fields."""

    name: str = Field(..., min_length=1, max_length=100, description="Server name")
    description: Optional[str] = Field(None, description="Server description")
    server_type: ServerType = Field(..., description="Minecraft server type")
    version: str = Field(..., min_length=1, max_length=20, description="Minecraft version")
    memory_mb: int = Field(2048, ge=512, le=32768, description="Memory allocation in MB")


class ServerCreate(ServerBase):
    """Schema for creating a new server."""

    port: Optional[int] = Field(
        None,
        ge=1024,
        le=65535,
        description="Server port (auto-assigned if not provided)"
    )
    rcon_port: Optional[int] = Field(
        None,
        ge=1024,
        le=65535,
        description="RCON port (auto-assigned if not provided)"
    )

    @field_validator('port', 'rcon_port')
    @classmethod
    def validate_ports(cls, v):
        if v is not None and (v < 1024 or v > 65535):
            raise ValueError("Port must be between 1024 and 65535")
        return v


class ServerUpdate(BaseModel):
    """Schema for updating an existing server."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    memory_mb: Optional[int] = Field(None, ge=512, le=32768)


class ServerResponse(ServerBase):
    """Complete server data for API responses."""

    id: int
    port: int
    rcon_port: int
    container_id: Optional[str] = None
    container_name: str
    status: ServerStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_started_at: Optional[datetime] = None
    last_stopped_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ServerList(BaseModel):
    """Simplified server data for list views."""

    id: int
    name: str
    description: Optional[str] = None
    server_type: ServerType
    version: str
    port: int
    status: ServerStatus
    is_active: bool
    memory_mb: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServerStats(BaseModel):
    """Real-time server statistics."""

    server_id: int
    status: ServerStatus
    online_players: int = 0
    max_players: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    memory_limit: float = 0.0
    uptime_seconds: int = 0
