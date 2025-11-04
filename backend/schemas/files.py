"""
Pydantic schemas for file operations.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    """File type enumeration."""
    FILE = "file"
    DIRECTORY = "directory"


class FileInfo(BaseModel):
    """File/directory information."""
    name: str = Field(..., description="File or directory name")
    path: str = Field(..., description="Full path relative to /data")
    type: FileType = Field(..., description="File or directory")
    size: int = Field(0, description="File size in bytes (0 for directories)")
    modified: Optional[datetime] = Field(None, description="Last modified timestamp")
    is_editable: bool = Field(False, description="Whether file can be edited in browser")
    extension: Optional[str] = Field(None, description="File extension without dot")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "server.properties",
                "path": "/server.properties",
                "type": "file",
                "size": 1024,
                "modified": "2025-01-04T12:00:00",
                "is_editable": True,
                "extension": "properties"
            }
        }


class FileListResponse(BaseModel):
    """Response for listing files in a directory."""
    path: str = Field(..., description="Current directory path")
    files: List[FileInfo] = Field(default_factory=list, description="List of files and directories")
    total: int = Field(0, description="Total number of items")

    class Config:
        json_schema_extra = {
            "example": {
                "path": "/",
                "files": [],
                "total": 5
            }
        }


class FileUploadResponse(BaseModel):
    """Response after uploading a file."""
    success: bool = Field(..., description="Whether upload was successful")
    path: str = Field(..., description="Path where file was uploaded")
    size: int = Field(..., description="Size of uploaded file in bytes")
    message: str = Field(..., description="Success or error message")


class FileDeleteRequest(BaseModel):
    """Request to delete a file or directory."""
    path: str = Field(..., description="Path to file or directory to delete")

    @field_validator('path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate that path doesn't contain path traversal."""
        if '..' in v:
            raise ValueError("Path traversal is not allowed")
        if not v.startswith('/'):
            v = '/' + v
        return v


class FileRenameRequest(BaseModel):
    """Request to rename a file or directory."""
    old_path: str = Field(..., description="Current path")
    new_name: str = Field(..., description="New name (not full path)")

    @field_validator('old_path')
    @classmethod
    def validate_old_path(cls, v: str) -> str:
        """Validate old path."""
        if '..' in v:
            raise ValueError("Path traversal is not allowed")
        if not v.startswith('/'):
            v = '/' + v
        return v

    @field_validator('new_name')
    @classmethod
    def validate_new_name(cls, v: str) -> str:
        """Validate new name."""
        if '/' in v or '..' in v:
            raise ValueError("New name cannot contain path separators or ..")
        return v


class CreateFolderRequest(BaseModel):
    """Request to create a new folder."""
    path: str = Field(..., description="Path where to create folder")
    name: str = Field(..., description="Folder name")

    @field_validator('path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate path."""
        if '..' in v:
            raise ValueError("Path traversal is not allowed")
        if not v.startswith('/'):
            v = '/' + v
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate folder name."""
        if '/' in v or '..' in v:
            raise ValueError("Folder name cannot contain path separators or ..")
        return v


class FileContentResponse(BaseModel):
    """Response with file content for editing."""
    path: str = Field(..., description="File path")
    content: str = Field(..., description="File content as text")
    size: int = Field(..., description="File size in bytes")
    is_binary: bool = Field(False, description="Whether file is binary")


class FileContentUpdate(BaseModel):
    """Request to update file content."""
    path: str = Field(..., description="File path")
    content: str = Field(..., description="New file content")

    @field_validator('path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate path."""
        if '..' in v:
            raise ValueError("Path traversal is not allowed")
        if not v.startswith('/'):
            v = '/' + v
        return v
