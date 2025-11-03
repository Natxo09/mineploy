"""
Tests for server properties endpoints.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from models.server import ServerType, ServerStatus
from schemas.properties import ServerPropertiesResponse


@pytest.fixture
async def test_server_with_container(test_db: AsyncSession, admin_user):
    """Create a test server with container."""
    from models.server import Server

    server = Server(
        name="Test Server",
        description="A test Minecraft server",
        server_type=ServerType.VANILLA,
        version="1.20.1",
        port=25565,
        rcon_port=25575,
        rcon_password="testpassword",
        memory_mb=2048,
        container_name="minecraft_test_server",
        container_id="test_container_id_123",
        status=ServerStatus.RUNNING,
    )
    test_db.add(server)
    await test_db.commit()
    await test_db.refresh(server)
    return server


@pytest.fixture
def mock_properties_response():
    """Mock server properties response."""
    return ServerPropertiesResponse(
        # Server settings
        motd="A Minecraft Server",
        max_players=20,
        server_port=25565,
        # Gameplay settings
        gamemode="survival",
        difficulty="normal",
        hardcore=False,
        pvp=True,
        # World settings
        level_name="world",
        level_seed="",
        level_type="default",
        generate_structures=True,
        spawn_monsters=True,
        spawn_animals=True,
        spawn_npcs=True,
        # Performance settings
        view_distance=10,
        simulation_distance=10,
        max_tick_time=60000,
        # Network settings
        online_mode=True,
        enable_status=True,
        allow_flight=False,
        max_world_size=29999984,
        # Spawn settings
        spawn_protection=16,
        force_gamemode=False,
        # Other settings
        white_list=False,
        enforce_whitelist=False,
        resource_pack="",
        resource_pack_prompt="",
        require_resource_pack=False,
        enable_command_block=False,
        function_permission_level=2,
        op_permission_level=4,
        # RCON settings
        enable_rcon=True,
        rcon_port=25575,
        rcon_password="testpassword",
        # Query settings
        enable_query=False,
        query_port=25565,
    )


# GET SERVER PROPERTIES TESTS

@pytest.mark.asyncio
async def test_get_server_properties_success(
    client: AsyncClient,
    admin_token,
    test_server_with_container,
    mock_properties_response
):
    """Test getting server properties as admin."""
    with patch('services.server_properties_service.server_properties_service.get_properties', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_properties_response

        response = await client.get(
            f"/api/v1/servers/{test_server_with_container.id}/properties",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["motd"] == "A Minecraft Server"
        assert data["max_players"] == 20
        assert data["gamemode"] == "survival"
        assert data["difficulty"] == "normal"
        mock_get.assert_called_once_with(test_server_with_container.container_id)


@pytest.mark.asyncio
async def test_get_server_properties_no_auth(client: AsyncClient, test_server_with_container):
    """Test getting server properties without authentication."""
    response = await client.get(
        f"/api/v1/servers/{test_server_with_container.id}/properties"
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_server_properties_no_permission(
    client: AsyncClient,
    viewer_token,
    test_server_with_container
):
    """Test getting server properties without VIEW permission."""
    response = await client.get(
        f"/api/v1/servers/{test_server_with_container.id}/properties",
        headers={"Authorization": f"Bearer {viewer_token}"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_server_properties_with_view_permission(
    client: AsyncClient,
    viewer_token,
    test_server_with_container,
    test_db,
    viewer_user,
    mock_properties_response
):
    """Test getting server properties with VIEW permission."""
    from models.user_server_permission import UserServerPermission, ServerPermission

    # Grant VIEW permission
    permission = UserServerPermission(
        user_id=viewer_user.id,
        server_id=test_server_with_container.id,
        permissions=[ServerPermission.VIEW.value]
    )
    test_db.add(permission)
    await test_db.commit()

    with patch('services.server_properties_service.server_properties_service.get_properties', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_properties_response

        response = await client.get(
            f"/api/v1/servers/{test_server_with_container.id}/properties",
            headers={"Authorization": f"Bearer {viewer_token}"}
        )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_server_properties_server_not_found(client: AsyncClient, admin_token):
    """Test getting properties for non-existent server."""
    response = await client.get(
        "/api/v1/servers/999/properties",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_server_properties_no_container(client: AsyncClient, admin_token, test_db, admin_user):
    """Test getting properties for server without container."""
    from models.server import Server
    from sqlalchemy import select, func

    # Find an available port
    result = await test_db.execute(select(func.max(Server.port)))
    max_port = result.scalar() or 25565
    new_port = max_port + 1
    new_rcon_port = max_port + 11

    server = Server(
        name="No Container Server",
        description="Server without container",
        server_type=ServerType.VANILLA,
        version="1.20.1",
        port=new_port,
        rcon_port=new_rcon_port,
        rcon_password="testpassword",
        memory_mb=2048,
        container_name="minecraft_no_container",
        container_id=None,
        status=ServerStatus.STOPPED,
    )
    test_db.add(server)
    await test_db.commit()
    await test_db.refresh(server)

    response = await client.get(
        f"/api/v1/servers/{server.id}/properties",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_server_properties_file_not_found(
    client: AsyncClient,
    admin_token,
    test_server_with_container
):
    """Test getting properties when file doesn't exist in container."""
    with patch('services.server_properties_service.server_properties_service.get_properties', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = FileNotFoundError("server.properties not found")

        response = await client.get(
            f"/api/v1/servers/{test_server_with_container.id}/properties",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404


# UPDATE SERVER PROPERTIES TESTS

@pytest.mark.asyncio
async def test_update_server_properties_success(
    client: AsyncClient,
    admin_token,
    test_server_with_container,
    mock_properties_response
):
    """Test updating server properties as admin."""
    with patch('services.server_properties_service.server_properties_service.update_properties', new_callable=AsyncMock) as mock_update:
        # Update mock response with new values
        updated_response = mock_properties_response.model_copy()
        updated_response.motd = "Updated MOTD"
        updated_response.max_players = 50
        mock_update.return_value = updated_response

        response = await client.patch(
            f"/api/v1/servers/{test_server_with_container.id}/properties",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "motd": "Updated MOTD",
                "max_players": 50
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["motd"] == "Updated MOTD"
        assert data["max_players"] == 50
        mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_update_server_properties_no_auth(client: AsyncClient, test_server_with_container):
    """Test updating server properties without authentication."""
    response = await client.patch(
        f"/api/v1/servers/{test_server_with_container.id}/properties",
        json={"motd": "New MOTD"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_server_properties_no_permission(
    client: AsyncClient,
    viewer_token,
    test_server_with_container
):
    """Test updating server properties without MANAGE permission."""
    response = await client.patch(
        f"/api/v1/servers/{test_server_with_container.id}/properties",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"motd": "New MOTD"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_server_properties_with_manage_permission(
    client: AsyncClient,
    viewer_token,
    test_server_with_container,
    test_db,
    viewer_user,
    mock_properties_response
):
    """Test updating server properties with MANAGE permission."""
    from models.user_server_permission import UserServerPermission, ServerPermission

    # Grant MANAGE permission
    permission = UserServerPermission(
        user_id=viewer_user.id,
        server_id=test_server_with_container.id,
        permissions=[ServerPermission.MANAGE.value]
    )
    test_db.add(permission)
    await test_db.commit()

    with patch('services.server_properties_service.server_properties_service.update_properties', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = mock_properties_response

        response = await client.patch(
            f"/api/v1/servers/{test_server_with_container.id}/properties",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={"motd": "New MOTD"}
        )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_server_properties_invalid_gamemode(
    client: AsyncClient,
    admin_token,
    test_server_with_container
):
    """Test updating properties with invalid gamemode."""
    response = await client.patch(
        f"/api/v1/servers/{test_server_with_container.id}/properties",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"gamemode": "invalid_mode"}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_server_properties_invalid_difficulty(
    client: AsyncClient,
    admin_token,
    test_server_with_container
):
    """Test updating properties with invalid difficulty."""
    response = await client.patch(
        f"/api/v1/servers/{test_server_with_container.id}/properties",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"difficulty": "super_hard"}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_server_properties_invalid_max_players(
    client: AsyncClient,
    admin_token,
    test_server_with_container
):
    """Test updating properties with invalid max_players."""
    response = await client.patch(
        f"/api/v1/servers/{test_server_with_container.id}/properties",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"max_players": -1}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_server_properties_multiple_fields(
    client: AsyncClient,
    admin_token,
    test_server_with_container,
    mock_properties_response
):
    """Test updating multiple properties at once."""
    with patch('services.server_properties_service.server_properties_service.update_properties', new_callable=AsyncMock) as mock_update:
        updated_response = mock_properties_response.model_copy()
        updated_response.motd = "New Server"
        updated_response.max_players = 100
        updated_response.difficulty = "hard"
        updated_response.pvp = False
        mock_update.return_value = updated_response

        response = await client.patch(
            f"/api/v1/servers/{test_server_with_container.id}/properties",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "motd": "New Server",
                "max_players": 100,
                "difficulty": "hard",
                "pvp": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["motd"] == "New Server"
        assert data["max_players"] == 100
        assert data["difficulty"] == "hard"
        assert data["pvp"] is False
