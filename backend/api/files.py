"""
API endpoints for file management in Minecraft servers.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import io

from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from models.server import Server
from models.user_server_permission import ServerPermission
from schemas.files import (
    FileListResponse,
    FileInfo,
    FileUploadResponse,
    FileDeleteRequest,
    FileRenameRequest,
    CreateFolderRequest,
    FileContentResponse,
    FileContentUpdate,
)
from services.file_service import file_service
from services.permission_service import PermissionService

router = APIRouter()


async def _get_server_with_permission(
    server_id: int,
    user: User,
    required_permission: ServerPermission,
    db: AsyncSession,
) -> Server:
    """
    Get server and verify user has required permission.

    Args:
        server_id: Server ID
        user: Current user
        required_permission: Required permission level
        db: Database session

    Returns:
        Server object

    Raises:
        HTTPException: If server not found or permission denied
    """
    # Get server
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    # Check permission
    has_permission = await PermissionService.has_server_permission(
        user=user,
        server_id=server_id,
        permission=required_permission,
        db=db,
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access files on this server",
        )

    # Check if server has a container
    if not server.container_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server has no container",
        )

    return server


@router.get("/{server_id}/files", response_model=FileListResponse)
async def list_files(
    server_id: int,
    path: str = Query("/", description="Directory path to list"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List files in a directory within the server container.

    Requires FILES permission.
    """
    print(f"[DEBUG API] list_files endpoint called - server_id={server_id}, path={path}, user={current_user.username}")

    try:
        server = await _get_server_with_permission(
            server_id=server_id,
            user=current_user,
            required_permission=ServerPermission.FILES,
            db=db,
        )
        print(f"[DEBUG API] Got server with permission - server.id={server.id}, container_id={server.container_id}")

    except HTTPException as e:
        print(f"[ERROR API] Permission check failed: {e.detail}")
        raise
    except Exception as e:
        print(f"[ERROR API] Unexpected error in permission check: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

    try:
        print(f"[DEBUG API] Calling file_service.list_files with container_id={server.container_id}, path={path}")
        files = await file_service.list_files(server.container_id, path)
        print(f"[DEBUG API] file_service.list_files returned {len(files)} files")

        return FileListResponse(
            path=path,
            files=files,
            total=len(files),
        )

    except FileNotFoundError as e:
        print(f"[ERROR API] FileNotFoundError: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        print(f"[ERROR API] ValueError: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(f"[ERROR API] Unexpected error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}",
        )


@router.get("/{server_id}/files/content", response_model=FileContentResponse)
async def get_file_content(
    server_id: int,
    path: str = Query(..., description="File path to read"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get file content for editing in browser.

    Only works with text files. Requires FILES permission.
    """
    server = await _get_server_with_permission(
        server_id=server_id,
        user=current_user,
        required_permission=ServerPermission.FILES,
        db=db,
    )

    try:
        content_bytes = await file_service.read_file(server.container_id, path)

        # Try to decode as UTF-8 text
        try:
            content = content_bytes.decode('utf-8')
            is_binary = False
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is binary and cannot be edited in browser",
            )

        return FileContentResponse(
            path=path,
            content=content,
            size=len(content_bytes),
            is_binary=is_binary,
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {str(e)}",
        )


@router.put("/{server_id}/files/content")
async def update_file_content(
    server_id: int,
    update: FileContentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update file content.

    Requires FILES permission.
    """
    server = await _get_server_with_permission(
        server_id=server_id,
        user=current_user,
        required_permission=ServerPermission.FILES,
        db=db,
    )

    try:
        content_bytes = update.content.encode('utf-8')
        await file_service.write_file(server.container_id, update.path, content_bytes)

        return {"success": True, "message": "File updated successfully"}

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update file: {str(e)}",
        )


@router.get("/{server_id}/files/download")
async def download_file(
    server_id: int,
    path: str = Query(..., description="File path to download"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Download a file from the server container.

    Requires FILES permission.
    """
    server = await _get_server_with_permission(
        server_id=server_id,
        user=current_user,
        required_permission=ServerPermission.FILES,
        db=db,
    )

    try:
        content = await file_service.read_file(server.container_id, path)

        # Get filename
        import os
        filename = os.path.basename(path)

        return Response(
            content=content,
            media_type='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}",
        )


@router.post("/{server_id}/files/upload", response_model=FileUploadResponse)
async def upload_file(
    server_id: int,
    file: UploadFile = File(...),
    path: str = Query("/", description="Directory path where to upload"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a file to the server container.

    Requires FILES permission.
    """
    server = await _get_server_with_permission(
        server_id=server_id,
        user=current_user,
        required_permission=ServerPermission.FILES,
        db=db,
    )

    try:
        # Read file content
        content = await file.read()

        # Build full path
        if path == '/':
            full_path = f"/{file.filename}"
        else:
            full_path = f"{path}/{file.filename}"

        # Write file
        await file_service.write_file(server.container_id, full_path, content)

        return FileUploadResponse(
            success=True,
            path=full_path,
            size=len(content),
            message="File uploaded successfully",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}",
        )


@router.delete("/{server_id}/files")
async def delete_file(
    server_id: int,
    request: FileDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a file or directory from the server container.

    Requires FILES permission.
    """
    server = await _get_server_with_permission(
        server_id=server_id,
        user=current_user,
        required_permission=ServerPermission.FILES,
        db=db,
    )

    try:
        await file_service.delete_file(server.container_id, request.path)

        return {"success": True, "message": "File deleted successfully"}

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}",
        )


@router.post("/{server_id}/files/folder")
async def create_folder(
    server_id: int,
    request: CreateFolderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new folder in the server container.

    Requires FILES permission.
    """
    server = await _get_server_with_permission(
        server_id=server_id,
        user=current_user,
        required_permission=ServerPermission.FILES,
        db=db,
    )

    try:
        await file_service.create_folder(server.container_id, request.path, request.name)

        # Build full path
        if request.path == '/':
            full_path = f"/{request.name}"
        else:
            full_path = f"{request.path}/{request.name}"

        return {"success": True, "message": "Folder created successfully", "path": full_path}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create folder: {str(e)}",
        )


@router.post("/{server_id}/files/rename")
async def rename_file(
    server_id: int,
    request: FileRenameRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Rename a file or directory in the server container.

    Requires FILES permission.
    """
    server = await _get_server_with_permission(
        server_id=server_id,
        user=current_user,
        required_permission=ServerPermission.FILES,
        db=db,
    )

    try:
        await file_service.rename_file(server.container_id, request.old_path, request.new_name)

        # Build new path
        import os
        parent_dir = os.path.dirname(request.old_path)
        if parent_dir == '':
            parent_dir = '/'

        if parent_dir == '/':
            new_path = f"/{request.new_name}"
        else:
            new_path = f"{parent_dir}/{request.new_name}"

        return {"success": True, "message": "File renamed successfully", "new_path": new_path}

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rename file: {str(e)}",
        )
