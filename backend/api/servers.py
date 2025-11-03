"""
API endpoints for Minecraft server management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
import secrets
import string

from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from models.server import Server, ServerStatus
from models.user_server_permission import ServerPermission
from schemas.server import (
    ServerCreate,
    ServerUpdate,
    ServerResponse,
    ServerList,
    ServerStats,
)
from services.docker_service import docker_service
from services.permission_service import PermissionService
from services.websocket_service import manager
from core.config import settings

router = APIRouter()


def _generate_rcon_password() -> str:
    """Generate a secure random RCON password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(32))


async def _find_available_port(db: AsyncSession, is_rcon: bool = False) -> int:
    """
    Find an available port in the configured range.

    Args:
        db: Database session
        is_rcon: If True, search RCON port range, else server port range

    Returns:
        Available port number

    Raises:
        HTTPException: If no ports available
    """
    if is_rcon:
        start = settings.rcon_port_range_start
        end = settings.rcon_port_range_end
        column = Server.rcon_port
    else:
        start = settings.server_port_range_start
        end = settings.server_port_range_end
        column = Server.port

    # Get all used ports
    result = await db.execute(select(column))
    used_ports = {port for (port,) in result.all()}

    # Find first available port
    for port in range(start, end + 1):
        if port not in used_ports:
            return port

    raise HTTPException(
        status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
        detail=f"No available {'RCON' if is_rcon else 'server'} ports in range {start}-{end}"
    )


@router.post("", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    server_data: ServerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new Minecraft server.

    Requires ADMIN role.
    """
    # Only admins can create servers
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create servers"
        )

    # Check max servers limit
    result = await db.execute(select(func.count(Server.id)))
    server_count = result.scalar_one()

    if server_count >= settings.max_servers:
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail=f"Maximum number of servers ({settings.max_servers}) reached"
        )

    # Check if name already exists
    result = await db.execute(
        select(Server).where(Server.name == server_data.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Server with name '{server_data.name}' already exists"
        )

    # Assign ports if not provided
    port = server_data.port
    if not port:
        port = await _find_available_port(db, is_rcon=False)

    rcon_port = server_data.rcon_port
    if not rcon_port:
        rcon_port = await _find_available_port(db, is_rcon=True)

    # Check if ports are already in use
    if server_data.port:
        result = await db.execute(select(Server).where(Server.port == server_data.port))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Port {server_data.port} is already in use"
            )

    if server_data.rcon_port:
        result = await db.execute(select(Server).where(Server.rcon_port == server_data.rcon_port))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"RCON port {server_data.rcon_port} is already in use"
            )

    # Generate RCON password
    rcon_password = _generate_rcon_password()

    # Generate unique container name
    container_name = f"minecraft_{server_data.name.lower().replace(' ', '_')}"

    # Check if container name exists
    if await docker_service.container_exists(container_name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Container '{container_name}' already exists"
        )

    # Create server in database first
    new_server = Server(
        name=server_data.name,
        description=server_data.description,
        server_type=server_data.server_type,
        version=server_data.version,
        port=port,
        rcon_port=rcon_port,
        rcon_password=rcon_password,
        memory_mb=server_data.memory_mb,
        container_name=container_name,
        status=ServerStatus.STOPPED,
    )

    db.add(new_server)
    await db.commit()
    await db.refresh(new_server)

    try:
        # Step 1: Pull Docker image with progress tracking
        new_server.status = ServerStatus.DOWNLOADING
        await db.commit()
        await db.refresh(new_server)
        await manager.broadcast_status_update(new_server.id, "downloading", {"message": "Downloading Docker image..."})

        async def on_pull_progress(progress_data: dict):
            """Callback to emit pull progress via WebSocket."""
            # Extract relevant progress info
            status_msg = progress_data.get("status", "")
            progress_detail = progress_data.get("progressDetail", {})

            # Build log message
            log_msg = status_msg
            if progress_detail:
                current = progress_detail.get("current", 0)
                total = progress_detail.get("total", 0)
                if total > 0:
                    percentage = (current / total) * 100
                    log_msg = f"{status_msg} {percentage:.1f}%"

            # Emit log to WebSocket
            await manager.broadcast_container_logs(new_server.id, log_msg)

        # Pull the image
        await docker_service.pull_image_with_progress(
            image="itzg/minecraft-server:latest",
            on_progress=on_pull_progress
        )

        # Step 2: Create container
        new_server.status = ServerStatus.INITIALIZING
        await db.commit()
        await db.refresh(new_server)
        await manager.broadcast_status_update(new_server.id, "initializing", {"message": "Creating container..."})

        container_id, container_info = await docker_service.create_container(
            container_name=container_name,
            server_type=server_data.server_type,
            version=server_data.version,
            port=port,
            rcon_port=rcon_port,
            rcon_password=rcon_password,
            memory_mb=server_data.memory_mb,
        )

        # Update server with container ID and set to STOPPED
        new_server.container_id = container_id
        new_server.status = ServerStatus.STOPPED
        await db.commit()
        await db.refresh(new_server)
        await manager.broadcast_status_update(new_server.id, "stopped", {"message": "Server created successfully"})

        return new_server

    except Exception as e:
        # Rollback: Delete server from database if container creation fails
        await db.delete(new_server)
        await db.commit()

        # Broadcast error
        await manager.broadcast_status_update(
            new_server.id,
            "error",
            {"message": f"Failed to create server: {str(e)}"}
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create server container: {str(e)}"
        )


@router.get("", response_model=List[ServerList])
async def list_servers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all accessible Minecraft servers.

    Returns servers based on user permissions:
    - ADMIN: All servers
    - MODERATOR: All servers (read-only for non-assigned)
    - VIEWER: Only assigned servers
    """
    # Get accessible server IDs based on permissions
    server_ids = await PermissionService.get_accessible_servers(current_user, db)

    # Fetch servers
    result = await db.execute(select(Server).where(Server.id.in_(server_ids)))
    servers = result.scalars().all()

    return servers


@router.get("/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get details of a specific server.

    Requires VIEW permission or higher.
    """
    # Get server
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID {server_id} not found"
        )

    # Check permissions
    if not await PermissionService.has_server_permission(
        current_user, server_id, ServerPermission.VIEW, db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this server"
        )

    # Update status from Docker
    if server.container_id:
        server.status = await docker_service.get_container_status(server.container_id)
        await db.commit()

    return server


@router.put("/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: int,
    server_update: ServerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update server settings.

    Requires MANAGE permission.
    Note: Server must be stopped to update settings.
    """
    # Get server
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID {server_id} not found"
        )

    # Check permissions
    if not await PermissionService.has_server_permission(
        current_user, server_id, ServerPermission.MANAGE, db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage this server"
        )

    # Check if server is stopped
    if server.status != ServerStatus.STOPPED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Server must be stopped to update settings"
        )

    # Update fields
    if server_update.name is not None:
        # Check if new name already exists
        result = await db.execute(
            select(Server).where(
                Server.name == server_update.name,
                Server.id != server_id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Server with name '{server_update.name}' already exists"
            )
        server.name = server_update.name

    if server_update.description is not None:
        server.description = server_update.description

    if server_update.memory_mb is not None:
        server.memory_mb = server_update.memory_mb

    await db.commit()
    await db.refresh(server)

    return server


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a server and its container.

    Requires MANAGE permission.
    """
    # Get server
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID {server_id} not found"
        )

    # Check permissions
    if not await PermissionService.has_server_permission(
        current_user, server_id, ServerPermission.MANAGE, db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage this server"
        )

    # Delete Docker container if exists
    if server.container_id:
        try:
            await docker_service.delete_container(server.container_id, force=True)
        except Exception as e:
            # Log error but continue with database deletion
            print(f"Warning: Failed to delete container {server.container_id}: {e}")

    # Delete server from database (cascade will delete permissions)
    await db.delete(server)
    await db.commit()


@router.post("/{server_id}/start", response_model=ServerResponse)
async def start_server(
    server_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a Minecraft server.

    Requires START_STOP permission or higher.
    """
    # Get server
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID {server_id} not found"
        )

    # Check permissions
    if not await PermissionService.has_server_permission(
        current_user, server_id, ServerPermission.START_STOP, db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to start/stop this server"
        )

    # Check if already running
    if server.status == ServerStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Server is already running"
        )

    if not server.container_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server has no associated container"
        )

    try:
        # Update status to STARTING
        server.status = ServerStatus.STARTING
        await db.commit()

        # Start container
        await docker_service.start_container(server.container_id)

        # Update status and timestamp
        server.status = ServerStatus.RUNNING
        from datetime import datetime, timezone
        server.last_started_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
        await db.refresh(server)

        return server

    except Exception as e:
        server.status = ServerStatus.ERROR
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start server: {str(e)}"
        )


@router.post("/{server_id}/stop", response_model=ServerResponse)
async def stop_server(
    server_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Stop a Minecraft server.

    Requires START_STOP permission or higher.
    """
    # Get server
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID {server_id} not found"
        )

    # Check permissions
    if not await PermissionService.has_server_permission(
        current_user, server_id, ServerPermission.START_STOP, db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to start/stop this server"
        )

    # Check if already stopped
    if server.status == ServerStatus.STOPPED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Server is already stopped"
        )

    if not server.container_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server has no associated container"
        )

    try:
        # Update status to STOPPING
        server.status = ServerStatus.STOPPING
        await db.commit()

        # Stop container
        await docker_service.stop_container(server.container_id)

        # Update status and timestamp
        server.status = ServerStatus.STOPPED
        from datetime import datetime, timezone
        server.last_stopped_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
        await db.refresh(server)

        return server

    except Exception as e:
        server.status = ServerStatus.ERROR
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop server: {str(e)}"
        )


@router.post("/{server_id}/restart", response_model=ServerResponse)
async def restart_server(
    server_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Restart a Minecraft server.

    Requires START_STOP permission or higher.
    """
    # Get server
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID {server_id} not found"
        )

    # Check permissions
    if not await PermissionService.has_server_permission(
        current_user, server_id, ServerPermission.START_STOP, db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to start/stop this server"
        )

    if not server.container_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server has no associated container"
        )

    try:
        # Update status to STARTING
        server.status = ServerStatus.STARTING
        await db.commit()

        # Restart container
        await docker_service.restart_container(server.container_id)

        # Update status and timestamp
        server.status = ServerStatus.RUNNING
        from datetime import datetime, timezone
        server.last_started_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
        await db.refresh(server)

        return server

    except Exception as e:
        server.status = ServerStatus.ERROR
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart server: {str(e)}"
        )


@router.get("/{server_id}/stats", response_model=ServerStats)
async def get_server_stats(
    server_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get real-time server statistics.

    Requires VIEW permission or higher.
    """
    # Get server
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID {server_id} not found"
        )

    # Check permissions
    if not await PermissionService.has_server_permission(
        current_user, server_id, ServerPermission.VIEW, db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this server"
        )

    # Get stats from Docker
    stats_data = {
        "server_id": server_id,
        "status": server.status,
        "online_players": 0,  # TODO: Implement RCON query
        "max_players": 20,  # TODO: Get from server.properties
        "cpu_usage": 0.0,
        "memory_usage": 0.0,
        "memory_limit": float(server.memory_mb),
        "uptime_seconds": 0,
    }

    if server.container_id and server.status == ServerStatus.RUNNING:
        docker_stats = await docker_service.get_container_stats(server.container_id)
        if docker_stats:
            stats_data.update({
                "cpu_usage": docker_stats["cpu_percent"],
                "memory_usage": docker_stats["memory_usage_mb"],
                "memory_limit": docker_stats["memory_limit_mb"],
            })

    return ServerStats(**stats_data)


@router.websocket("/ws/{server_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    server_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for real-time server updates.

    Args:
        websocket: WebSocket connection
        server_id: Server ID to subscribe to
        db: Database session

    Note:
        Authentication is handled via query parameters or headers.
        The client should send the access token in the query string.
    """
    # Verify server exists
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        await websocket.close(code=1008, reason="Server not found")
        return

    # TODO: Add authentication check for WebSocket
    # For now, we'll accept all connections
    # In production, verify the user has VIEW permission for this server

    await manager.connect(websocket, server_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Echo back or handle ping/pong
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, server_id)
