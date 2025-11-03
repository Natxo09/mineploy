"""
Pydantic schemas for console/RCON operations.
"""

from pydantic import BaseModel, Field


class CommandRequest(BaseModel):
    """Schema for executing a command via RCON."""

    command: str = Field(..., min_length=1, max_length=500, description="Command to execute")


class CommandResponse(BaseModel):
    """Schema for command execution response."""

    command: str
    response: str
    success: bool = True


class PlayerListResponse(BaseModel):
    """Schema for player list response."""

    online_players: int
    max_players: int
    players: list[str]
