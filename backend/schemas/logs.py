"""
Schemas for log-related API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class LogFileInfo(BaseModel):
    """Information about a single log file."""

    name: str = Field(..., description="Filename (e.g., 'latest.log', '2024-01-15-1.log.gz')")
    size: int = Field(..., description="File size in bytes")
    modified_time: str = Field(..., description="Last modified timestamp (ISO format)")
    is_compressed: bool = Field(..., description="Whether the file is gzip compressed")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "2024-01-15-1.log.gz",
                "size": 1048576,
                "modified_time": "2024-01-15T10:30:00",
                "is_compressed": True,
            }
        }


class LogFileListResponse(BaseModel):
    """Response containing list of available log files."""

    files: List[LogFileInfo] = Field(..., description="List of log files")
    total: int = Field(..., description="Total number of log files")

    class Config:
        json_schema_extra = {
            "example": {
                "files": [
                    {
                        "name": "latest.log",
                        "size": 524288,
                        "modified_time": "2024-01-16T14:23:00",
                        "is_compressed": False,
                    },
                    {
                        "name": "2024-01-15-1.log.gz",
                        "size": 1048576,
                        "modified_time": "2024-01-15T10:30:00",
                        "is_compressed": True,
                    },
                ],
                "total": 2,
            }
        }


class LogFileContentResponse(BaseModel):
    """Response containing log file content."""

    filename: str = Field(..., description="Name of the log file")
    content: str = Field(..., description="Log file content")
    lines: int = Field(..., description="Number of lines in the content")
    size: int = Field(..., description="Size of the content in bytes")

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "latest.log",
                "content": "[Server thread/INFO]: Starting minecraft server...\n[Server thread/INFO]: Done!",
                "lines": 2,
                "size": 85,
            }
        }


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
