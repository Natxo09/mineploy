"""
API endpoints for Minecraft server management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
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
from schemas.properties import (
    ServerPropertiesResponse,
    ServerPropertiesUpdate,
)
from schemas.logs import LogsResponse
from services.docker_service import docker_service
from services.permission_service import PermissionService
from services.websocket_service import manager
from services.rcon_service import rcon_service
from services.query_service import query_service
from services.properties_parser import properties_parser
from services.server_properties_service import server_properties_service
from services.minecraft_logs_service import minecraft_logs_service
from core.config import settings

router = APIRouter()

# Import after router to avoid circular imports
from api.settings import get_or_create_settings


def _generate_rcon_password() -> str:
    """Generate a secure random RCON password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(32))


async def _find_available_port(db: AsyncSession, port_type: str = "server") -> int:
    """
    Find an available port in the configured range.

    Args:
        db: Database session
        port_type: Type of port to find ("server", "rcon", or "query")

    Returns:
        Available port number

    Raises:
        HTTPException: If no ports available
    """
    if port_type == "rcon":
        start = settings.rcon_port_range_start
        end = settings.rcon_port_range_end
        column = Server.rcon_port
    elif port_type == "query":
        start = settings.query_port_range_start
        end = settings.query_port_range_end
        column = Server.query_port
    else:  # "server"
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
        detail=f"No available {port_type} ports in range {start}-{end}"
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
        port = await _find_available_port(db, port_type="server")

    rcon_port = server_data.rcon_port
    if not rcon_port:
        rcon_port = await _find_available_port(db, port_type="rcon")

    query_port = server_data.query_port
    if not query_port:
        query_port = await _find_available_port(db, port_type="query")

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

    if server_data.query_port:
        result = await db.execute(select(Server).where(Server.query_port == server_data.query_port))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Query port {server_data.query_port} is already in use"
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
        query_port=query_port,
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
            try:
                # Extract relevant progress info
                status_msg = progress_data.get("status", "")
                progress_detail = progress_data.get("progressDetail", {})

                # Skip empty status messages
                if not status_msg:
                    return

                # Build log message
                log_msg = status_msg
                if progress_detail and isinstance(progress_detail, dict):
                    current = progress_detail.get("current", 0)
                    total = progress_detail.get("total", 0)
                    if total > 0:
                        percentage = (current / total) * 100
                        log_msg = f"{status_msg} {percentage:.1f}%"

                # Add layer ID if available for better context
                layer_id = progress_data.get("id")
                if layer_id:
                    log_msg = f"[{layer_id}] {log_msg}"

                # Emit log to WebSocket
                await manager.broadcast_container_logs(new_server.id, log_msg)
            except Exception as e:
                # Log error but don't break the pull process
                print(f"⚠️  Error processing pull progress: {e}")

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

        # Get system timezone for container
        sys_settings = await get_or_create_settings(db)

        container_id, container_info = await docker_service.create_container(
            container_name=container_name,
            server_type=server_data.server_type,
            version=server_data.version,
            port=port,
            rcon_port=rcon_port,
            rcon_password=rcon_password,
            query_port=query_port,
            memory_mb=server_data.memory_mb,
            timezone=sys_settings.timezone,
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
        server.has_been_started = True
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
        server.has_been_started = True
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

    # Initialize stats data
    stats_data = {
        "server_id": server_id,
        "status": server.status,
        "online_players": 0,
        "max_players": 20,
        "cpu_usage": 0.0,
        "memory_usage": 0.0,
        "memory_limit": float(server.memory_mb),
        "uptime_seconds": 0,
    }

    if server.container_id and server.status == ServerStatus.RUNNING:
        # Get Docker stats (CPU, RAM, uptime)
        try:
            docker_stats = await docker_service.get_container_stats(server.container_id)
            if docker_stats:
                stats_data.update({
                    "cpu_usage": docker_stats["cpu_percent"],
                    "memory_usage": docker_stats["memory_usage_mb"],
                    "memory_limit": docker_stats["memory_limit_mb"],
                })

                # Calculate uptime from last_started_at
                if server.last_started_at:
                    from datetime import datetime, timezone as tz
                    # Ensure both datetimes are timezone-aware
                    now_utc = datetime.now(tz.utc)
                    started_at = server.last_started_at

                    # If last_started_at is naive, assume it's UTC
                    if started_at.tzinfo is None:
                        started_at = started_at.replace(tzinfo=tz.utc)

                    uptime_delta = now_utc - started_at
                    stats_data["uptime_seconds"] = int(uptime_delta.total_seconds())
        except Exception as e:
            # Docker might not be available, keep default values
            print(f"⚠️  Failed to get Docker stats for server {server_id}: {e}")

        # Get player data via Query Protocol (no log spam!)
        try:
            print(f"📊 [STATS] Getting player count for server {server_id} via Query Protocol (port: {server.query_port})")
            # Use container name instead of localhost when backend is in Docker
            player_data = await query_service.get_player_count(
                host=server.container_name,
                port=server.query_port,
            )
            stats_data.update({
                "online_players": player_data["online_players"],
                "max_players": player_data["max_players"],
            })
        except Exception as e:
            # Query might not be ready yet, keep default values
            print(f"⚠️  Failed to get player count for server {server_id}: {e}")

    return ServerStats(**stats_data)


@router.get("/{server_id}/logs", response_model=LogsResponse)
async def get_server_logs(
    server_id: int,
    tail: int = 500,
    filter_type: Optional[str] = None,
    since_start: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get server container logs.

    Requires VIEW permission or higher.

    Args:
        server_id: Server ID
        tail: Number of lines to retrieve (default: 500, max: 2000)
        filter_type: Filter logs by type: 'minecraft', 'docker', or None for all (default: None)
        since_start: If True, only get logs since last_started_at (default: False)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Container logs as plain text
    """
    # Limit tail to prevent abuse
    tail = min(tail, 2000)

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

    # Check if server has a container
    if not server.container_id:
        return LogsResponse(
            logs="No container found. Server may not have been started yet.",
            lines=1,
            filtered=filter_type
        )

    try:
        # Calculate since timestamp if requested
        since_timestamp = None
        if since_start and server.last_started_at:
            from datetime import timezone, datetime
            # Convert last_started_at to unix timestamp
            if server.last_started_at.tzinfo is None:
                # Assume UTC if naive
                started_at = server.last_started_at.replace(tzinfo=timezone.utc)
            else:
                started_at = server.last_started_at
            since_timestamp = int(started_at.timestamp())

            # Debug logging
            now = datetime.now(timezone.utc)
            print(f"🔍 DEBUG - Getting logs since start:")
            print(f"  - last_started_at: {server.last_started_at}")
            print(f"  - since_timestamp: {since_timestamp}")
            print(f"  - current time: {now}")
            print(f"  - time diff: {(now - started_at).total_seconds()} seconds ago")

        # Get container logs
        logs = await docker_service.get_container_logs(
            container_id=server.container_id,
            tail=tail if not since_start else None,  # Don't limit if filtering by time
            since=since_timestamp
        )

        # Debug: log what we got from Docker
        if logs:
            log_count = len(logs.split('\n'))
            print(f"📝 DEBUG - Got {log_count} lines from Docker (before filtering)")

        # Apply filtering if requested
        if filter_type == "minecraft":
            logs = minecraft_logs_service.filter_minecraft_logs(logs)
        elif filter_type == "docker":
            logs = minecraft_logs_service.filter_docker_logs(logs)

        # Count lines
        log_lines = logs.split("\n") if logs else []

        # Debug: log what we're returning after filtering
        print(f"✅ DEBUG - Returning {len(log_lines)} lines (after '{filter_type}' filtering)")

        return LogsResponse(
            logs=logs,
            lines=len(log_lines),
            filtered=filter_type
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve logs: {str(e)}"
        )


@router.post("/{server_id}/sync-properties", response_model=ServerResponse)
async def sync_server_properties(
    server_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sync server configuration from server.properties file.

    Reads the server.properties file from the Docker container and updates
    the database with the current RCON configuration. Useful when users
    manually edit the server.properties file.

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

    # Check if server has a container
    if not server.container_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server does not have a container yet"
        )

    try:
        # Read server.properties from container
        properties_content = await docker_service.read_file(
            server.container_id,
            "/data/server.properties"
        )

        if not properties_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="server.properties file not found in container. Server might not have started yet."
            )

        # Parse properties
        properties = properties_parser.parse(properties_content)
        rcon_config = properties_parser.get_rcon_config(properties)

        # Validate RCON config
        is_valid, error_msg = properties_parser.validate_rcon_config(rcon_config)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid RCON configuration: {error_msg}"
            )

        # Check if RCON port conflicts with another server
        if rcon_config['rcon_port'] != server.rcon_port:
            result = await db.execute(
                select(Server).where(
                    Server.rcon_port == rcon_config['rcon_port'],
                    Server.id != server_id
                )
            )
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"RCON port {rcon_config['rcon_port']} is already in use by another server"
                )

        # Update server with new RCON config
        server.rcon_port = rcon_config['rcon_port']
        server.rcon_password = rcon_config['rcon_password']

        await db.commit()
        await db.refresh(server)

        return server

    except HTTPException:
        raise
    except Exception as e:
        print(f"⚠️  Failed to sync properties for server {server_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync properties: {str(e)}"
        )


@router.get("/{server_id}/properties", response_model=ServerPropertiesResponse)
async def get_server_properties(
    server_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get server.properties configuration.

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

    # Check permissions (VIEW permission is enough to read properties)
    if not await PermissionService.has_server_permission(
        current_user, server_id, ServerPermission.VIEW, db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this server"
        )

    # Check if server has a container
    if not server.container_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server does not have a container yet"
        )

    # Check if server has been started at least once
    if not server.has_been_started:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server has not been started yet. Start the server at least once to generate server.properties file."
        )

    try:
        properties = await server_properties_service.get_properties(server.container_id)
        return properties

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="server.properties file not found. Server might not have started yet."
        )
    except Exception as e:
        print(f"⚠️  Failed to get properties for server {server_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get server properties: {str(e)}"
        )


@router.patch("/{server_id}/properties", response_model=ServerPropertiesResponse)
async def update_server_properties(
    server_id: int,
    updates: ServerPropertiesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update server.properties configuration.

    Note: Some changes (like world settings) only take effect for new worlds
    or after regenerating the world. Other changes require a server restart.

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

    # Check if server has a container
    if not server.container_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server does not have a container yet"
        )

    # Check if server has been started at least once
    if not server.has_been_started:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server has not been started yet. Start the server at least once to generate server.properties file."
        )

    try:
        properties = await server_properties_service.update_properties(
            server.container_id,
            updates
        )

        # Note: Server should be restarted for changes to take effect
        # We don't automatically restart to give users control

        return properties

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="server.properties file not found. Server might not have started yet."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        print(f"⚠️  Failed to update properties for server {server_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update server properties: {str(e)}"
        )


@router.websocket("/ws/{server_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    server_id: int,
    channel: str = "default",
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for real-time server updates.

    Supports multiple channels:
    - default: Status updates and generic messages
    - minecraft_logs: Real-time Minecraft server logs
    - container_logs: Real-time Docker container logs

    Args:
        websocket: WebSocket connection
        server_id: Server ID to subscribe to
        channel: Channel to subscribe to (default, minecraft_logs, container_logs)
        db: Database session

    Query parameters:
        ?channel=minecraft_logs  - Subscribe to Minecraft logs
        ?channel=container_logs  - Subscribe to container logs
        ?channel=default         - Subscribe to status updates (default)

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

    # Connect to the specific channel
    await manager.connect(websocket, server_id, channel)

    # Start log streaming if channel is for logs and server has container
    if channel in ["minecraft_logs", "container_logs"]:
        if server.container_id:
            log_type = "minecraft" if channel == "minecraft_logs" else "container"

            # Start streaming task (will only start if not already running)
            await manager.start_log_streaming(
                server_id=server_id,
                container_id=server.container_id,
                channel=channel,
                log_type=log_type
            )
        else:
            # Notify client that no container is available
            await websocket.send_json({
                "type": "error",
                "message": "No container available. Server has not been started yet.",
                "server_id": server_id
            })

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()

            # Handle ping/pong
            if data == "ping":
                await websocket.send_json({"type": "pong"})

            # Handle start/stop streaming commands
            elif data == "start_streaming" and channel in ["minecraft_logs", "container_logs"]:
                if server.container_id:
                    log_type = "minecraft" if channel == "minecraft_logs" else "container"
                    await manager.start_log_streaming(
                        server_id=server_id,
                        container_id=server.container_id,
                        channel=channel,
                        log_type=log_type
                    )
            elif data == "stop_streaming":
                manager.stop_log_streaming(server_id, channel)

    except WebSocketDisconnect:
        manager.disconnect(websocket, server_id, channel)
