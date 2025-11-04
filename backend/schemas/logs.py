"""
Schemas for log-related API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class LogsResponse(BaseModel):
    """Response for container logs endpoint (existing, enhanced)."""

    logs: str = Field(..., description="Log content")
    lines: int = Field(..., description="Number of lines")
    filtered: Optional[str] = Field(None, description="Filter applied (minecraft, docker, or none)")

    class Config:
        json_schema_extra = {
            "example": {
                "logs": "[Server thread/INFO]: Starting server...",
                "lines": 100,
                "filtered": "minecraft",
            }
        }
