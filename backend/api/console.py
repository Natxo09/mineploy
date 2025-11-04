"""
API endpoints for Minecraft server console/RCON operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from models.server import Server, ServerStatus
from models.user_server_permission import ServerPermission
from schemas.console import CommandRequest, CommandResponse, PlayerListResponse
from services.rcon_service import rcon_service
from services.permission_service import PermissionService

router = APIRouter()


@router.post("/{server_id}/command", response_model=CommandResponse)
async def execute_command(
    server_id: int,
    command_data: CommandRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute a command via RCON.

    Requires CONSOLE permission or higher.
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
        current_user, server_id, ServerPermission.CONSOLE, db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this server's console"
        )

    # Check if server is running
    if server.status != ServerStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Server must be running to execute commands"
        )

    try:
        # Execute command via RCON
        # Use container name instead of localhost when backend is in Docker
        response = await rcon_service.execute_command(
            host=server.container_name,
            port=server.rcon_port,
            password=server.rcon_password,
            command=command_data.command,
        )

        return CommandResponse(
            command=command_data.command,
            response=response,
            success=True,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute command: {str(e)}"
        )


@router.get("/{server_id}/players", response_model=PlayerListResponse)
async def get_players(
    server_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of online players.

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

    # Check if server is running
    if server.status != ServerStatus.RUNNING:
        return PlayerListResponse(
            online_players=0,
            max_players=20,
            players=[],
        )

    try:
        # Get player count and list
        # Use container name instead of localhost when backend is in Docker
        player_count = await rcon_service.get_player_count(
            host=server.container_name,
            port=server.rcon_port,
            password=server.rcon_password,
        )

        player_list = await rcon_service.get_online_players(
            host=server.container_name,
            port=server.rcon_port,
            password=server.rcon_password,
        )

        return PlayerListResponse(
            online_players=player_count["online_players"],
            max_players=player_count["max_players"],
            players=player_list,
        )

    except Exception as e:
        # Return empty list if RCON fails
        print(f"⚠️  Failed to get players for server {server_id}: {e}")
        return PlayerListResponse(
            online_players=0,
            max_players=20,
            players=[],
        )
