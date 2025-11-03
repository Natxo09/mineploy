"""
Tests for server management endpoints.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from models.server import ServerType, ServerStatus


@pytest.fixture
async def test_server(test_db: AsyncSession, admin_user):
    """Create a test server."""
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
        status=ServerStatus.STOPPED,
    )
    test_db.add(server)
    await test_db.commit()
    await test_db.refresh(server)
    return server


@pytest.fixture
async def viewer_server_permission(test_db: AsyncSession, viewer_user, test_server):
    """Grant VIEW permission to viewer on test server."""
    from models.user_server_permission import UserServerPermission, ServerPermission

    permission = UserServerPermission(
        user_id=viewer_user.id,
        server_id=test_server.id,
        permissions=[ServerPermission.VIEW.value]
    )
    test_db.add(permission)
    await test_db.commit()
    return permission


@pytest.fixture
async def viewer_manage_permission(test_db: AsyncSession, viewer_user, test_server):
    """Grant MANAGE permission to viewer on test server."""
    from models.user_server_permission import UserServerPermission, ServerPermission

    permission = UserServerPermission(
        user_id=viewer_user.id,
        server_id=test_server.id,
        permissions=[ServerPermission.MANAGE.value]
    )
    test_db.add(permission)
    await test_db.commit()
    return permission


# CREATE SERVER TESTS

@pytest.mark.asyncio
async def test_create_server_success(client: AsyncClient, admin_token):
    """Test creating a server as admin."""
    with patch('services.docker_service.docker_service.container_exists', new_callable=AsyncMock) as mock_exists, \
         patch('services.docker_service.docker_service.create_container', new_callable=AsyncMock) as mock_create:

        mock_exists.return_value = False
        mock_create.return_value = ("container_id_123", {"Id": "container_id_123"})

        response = await client.post(
            "/api/v1/servers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "New Server",
                "description": "Test description",
                "server_type": "vanilla",
                "version": "1.20.1",
                "memory_mb": 2048
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Server"
        assert data["server_type"] == "vanilla"
        assert data["version"] == "1.20.1"
        assert data["status"] == "stopped"
        assert "port" in data
        assert "rcon_port" in data


@pytest.mark.asyncio
async def test_create_server_with_custom_ports(client: AsyncClient, admin_token):
    """Test creating a server with custom ports."""
    with patch('services.docker_service.docker_service.container_exists', new_callable=AsyncMock) as mock_exists, \
         patch('services.docker_service.docker_service.create_container', new_callable=AsyncMock) as mock_create:

        mock_exists.return_value = False
        mock_create.return_value = ("container_id_456", {"Id": "container_id_456"})

        response = await client.post(
            "/api/v1/servers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Custom Port Server",
                "server_type": "paper",
                "version": "1.20.1",
                "port": 25566,
                "rcon_port": 25576,
                "memory_mb": 4096
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["port"] == 25566
        assert data["rcon_port"] == 25576
        assert data["memory_mb"] == 4096


@pytest.mark.asyncio
async def test_create_server_non_admin(client: AsyncClient, viewer_token):
    """Test creating a server as non-admin (should fail)."""
    response = await client.post(
        "/api/v1/servers",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={
            "name": "Should Fail",
            "server_type": "vanilla",
            "version": "1.20.1",
            "memory_mb": 2048
        }
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_server_duplicate_name(client: AsyncClient, admin_token, test_server):
    """Test creating a server with duplicate name."""
    response = await client.post(
        "/api/v1/servers",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Test Server",  # Same name as test_server
            "server_type": "vanilla",
            "version": "1.20.1",
            "memory_mb": 2048
        }
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_server_duplicate_port(client: AsyncClient, admin_token, test_server):
    """Test creating a server with duplicate port."""
    response = await client.post(
        "/api/v1/servers",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Different Server",
            "server_type": "vanilla",
            "version": "1.20.1",
            "port": 25565,  # Same port as test_server
            "memory_mb": 2048
        }
    )

    assert response.status_code == 409
    assert "Port 25565" in response.json()["detail"]


# LIST SERVERS TESTS

@pytest.mark.asyncio
async def test_list_servers_admin(client: AsyncClient, admin_token, test_server):
    """Test listing servers as admin."""
    response = await client.get(
        "/api/v1/servers",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_servers_viewer_with_permission(client: AsyncClient, viewer_token, test_server, viewer_server_permission):
    """Test listing servers as viewer with permission."""
    response = await client.get(
        "/api/v1/servers",
        headers={"Authorization": f"Bearer {viewer_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == test_server.id


@pytest.mark.asyncio
async def test_list_servers_no_auth(client: AsyncClient):
    """Test listing servers without authentication."""
    response = await client.get("/api/v1/servers")
    assert response.status_code == 403


# GET SERVER TESTS

@pytest.mark.asyncio
async def test_get_server_success(client: AsyncClient, admin_token, test_server):
    """Test getting a server by ID."""
    with patch('services.docker_service.docker_service.get_container_status', new_callable=AsyncMock) as mock_status:
        mock_status.return_value = ServerStatus.STOPPED

        response = await client.get(
            f"/api/v1/servers/{test_server.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_server.id
        assert data["name"] == test_server.name


@pytest.mark.asyncio
async def test_get_server_not_found(client: AsyncClient, admin_token):
    """Test getting non-existent server."""
    response = await client.get(
        "/api/v1/servers/99999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_server_no_permission(client: AsyncClient, viewer_token, test_server):
    """Test getting server without permission."""
    response = await client.get(
        f"/api/v1/servers/{test_server.id}",
        headers={"Authorization": f"Bearer {viewer_token}"}
    )

    assert response.status_code == 403


# UPDATE SERVER TESTS

@pytest.mark.asyncio
async def test_update_server_success(client: AsyncClient, admin_token, test_server):
    """Test updating a server."""
    response = await client.put(
        f"/api/v1/servers/{test_server.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Updated Server",
            "description": "Updated description",
            "memory_mb": 4096
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Server"
    assert data["description"] == "Updated description"
    assert data["memory_mb"] == 4096


@pytest.mark.asyncio
async def test_update_server_no_permission(client: AsyncClient, viewer_token, test_server, viewer_server_permission):
    """Test updating server without MANAGE permission."""
    response = await client.put(
        f"/api/v1/servers/{test_server.id}",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"name": "Should Fail"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_server_running(client: AsyncClient, admin_token, test_server, test_db: AsyncSession):
    """Test updating a running server (should fail)."""
    # Set server to RUNNING
    test_server.status = ServerStatus.RUNNING
    await test_db.commit()

    response = await client.put(
        f"/api/v1/servers/{test_server.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Should Fail"}
    )

    assert response.status_code == 409
    assert "must be stopped" in response.json()["detail"]


# DELETE SERVER TESTS

@pytest.mark.asyncio
async def test_delete_server_success(client: AsyncClient, admin_token, test_server):
    """Test deleting a server."""
    with patch('services.docker_service.docker_service.delete_container', new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = True

        response = await client.delete(
            f"/api/v1/servers/{test_server.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_server_no_permission(client: AsyncClient, viewer_token, test_server, viewer_server_permission):
    """Test deleting server without permission."""
    response = await client.delete(
        f"/api/v1/servers/{test_server.id}",
        headers={"Authorization": f"Bearer {viewer_token}"}
    )

    assert response.status_code == 403


# START SERVER TESTS

@pytest.mark.asyncio
async def test_start_server_success(client: AsyncClient, admin_token, test_server):
    """Test starting a server."""
    with patch('services.docker_service.docker_service.start_container', new_callable=AsyncMock) as mock_start:
        mock_start.return_value = True

        response = await client.post(
            f"/api/v1/servers/{test_server.id}/start",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"


@pytest.mark.asyncio
async def test_start_server_already_running(client: AsyncClient, admin_token, test_server, test_db: AsyncSession):
    """Test starting an already running server."""
    test_server.status = ServerStatus.RUNNING
    await test_db.commit()

    response = await client.post(
        f"/api/v1/servers/{test_server.id}/start",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 409
    assert "already running" in response.json()["detail"]


# STOP SERVER TESTS

@pytest.mark.asyncio
async def test_stop_server_success(client: AsyncClient, admin_token, test_server, test_db: AsyncSession):
    """Test stopping a server."""
    test_server.status = ServerStatus.RUNNING
    await test_db.commit()

    with patch('services.docker_service.docker_service.stop_container', new_callable=AsyncMock) as mock_stop:
        mock_stop.return_value = True

        response = await client.post(
            f"/api/v1/servers/{test_server.id}/stop",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"


@pytest.mark.asyncio
async def test_stop_server_already_stopped(client: AsyncClient, admin_token, test_server):
    """Test stopping an already stopped server."""
    response = await client.post(
        f"/api/v1/servers/{test_server.id}/stop",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 409
    assert "already stopped" in response.json()["detail"]


# RESTART SERVER TESTS

@pytest.mark.asyncio
async def test_restart_server_success(client: AsyncClient, admin_token, test_server):
    """Test restarting a server."""
    with patch('services.docker_service.docker_service.restart_container', new_callable=AsyncMock) as mock_restart:
        mock_restart.return_value = True

        response = await client.post(
            f"/api/v1/servers/{test_server.id}/restart",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"


# STATS TESTS

@pytest.mark.asyncio
async def test_get_server_stats(client: AsyncClient, admin_token, test_server, test_db: AsyncSession):
    """Test getting server statistics."""
    test_server.status = ServerStatus.RUNNING
    await test_db.commit()

    with patch('services.docker_service.docker_service.get_container_stats', new_callable=AsyncMock) as mock_stats:
        mock_stats.return_value = {
            "cpu_percent": 25.5,
            "memory_usage_mb": 1024.0,
            "memory_limit_mb": 2048.0,
            "memory_percent": 50.0
        }

        response = await client.get(
            f"/api/v1/servers/{test_server.id}/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["server_id"] == test_server.id
        assert data["status"] == "running"
        assert "cpu_usage" in data
        assert "memory_usage" in data


@pytest.mark.asyncio
async def test_get_server_stats_stopped(client: AsyncClient, admin_token, test_server):
    """Test getting stats for stopped server."""
    response = await client.get(
        f"/api/v1/servers/{test_server.id}/stats",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stopped"
    assert data["cpu_usage"] == 0.0
