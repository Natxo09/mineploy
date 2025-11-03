"""
Tests for console API endpoints.
"""

import pytest
from unittest.mock import patch
from mcrcon import MCRconException

from models.server import ServerStatus


@pytest.mark.asyncio
class TestConsoleEndpoints:
    """Test console/RCON API endpoints."""

    async def test_execute_command_success(self, client, test_server, test_db, admin_token):
        """Test successful command execution via RCON."""
        # Update server to running state
        test_server.status = ServerStatus.RUNNING
        test_db.add(test_server)
        await test_db.commit()

        mock_response = "Player1, Player2, Player3"

        with patch('services.rcon_service.rcon_service.execute_command', return_value=mock_response):
            response = await client.post(
                f"/api/v1/console/{test_server.id}/command",
                json={"command": "list"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["command"] == "list"
            assert data["response"] == mock_response
            assert data["success"] is True

    async def test_execute_command_server_not_running(self, client, test_server, admin_token):
        """Test command execution when server is not running."""
        # Ensure server is stopped
        assert test_server.status == ServerStatus.STOPPED

        response = await client.post(
            f"/api/v1/console/{test_server.id}/command",
            json={"command": "list"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 409
        assert "must be running" in response.json()["detail"]

    async def test_execute_command_server_not_found(self, client, admin_token):
        """Test command execution with non-existent server."""
        response = await client.post(
            "/api/v1/console/99999/command",
            json={"command": "list"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404

    async def test_execute_command_rcon_failure(self, client, test_server, test_db, admin_token):
        """Test command execution when RCON fails."""
        test_server.status = ServerStatus.RUNNING
        test_db.add(test_server)
        await test_db.commit()

        with patch('services.rcon_service.rcon_service.execute_command',
                   side_effect=MCRconException("Connection refused")):
            response = await client.post(
                f"/api/v1/console/{test_server.id}/command",
                json={"command": "list"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 500
            assert "Failed to execute command" in response.json()["detail"]

    async def test_execute_command_invalid_command(self, client, test_server, test_db, admin_token):
        """Test command execution with empty command."""
        test_server.status = ServerStatus.RUNNING
        test_db.add(test_server)
        await test_db.commit()

        response = await client.post(
            f"/api/v1/console/{test_server.id}/command",
            json={"command": ""},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 422  # Validation error

    async def test_get_players_success(self, client, test_server, test_db, admin_token):
        """Test getting player list successfully."""
        test_server.status = ServerStatus.RUNNING
        test_db.add(test_server)
        await test_db.commit()

        mock_player_count = {"online_players": 3, "max_players": 20}
        mock_player_list = ["Alice", "Bob", "Charlie"]

        with patch('services.rcon_service.rcon_service.get_player_count', return_value=mock_player_count), \
             patch('services.rcon_service.rcon_service.get_online_players', return_value=mock_player_list):

            response = await client.get(
                f"/api/v1/console/{test_server.id}/players",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["online_players"] == 3
            assert data["max_players"] == 20
            assert data["players"] == ["Alice", "Bob", "Charlie"]

    async def test_get_players_server_stopped(self, client, test_server, admin_token):
        """Test getting players when server is stopped."""
        assert test_server.status == ServerStatus.STOPPED

        response = await client.get(
            f"/api/v1/console/{test_server.id}/players",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["online_players"] == 0
        assert data["max_players"] == 20
        assert data["players"] == []

    async def test_get_players_no_players_online(self, client, test_server, test_db, admin_token):
        """Test getting players when none online."""
        test_server.status = ServerStatus.RUNNING
        test_db.add(test_server)
        await test_db.commit()

        mock_player_count = {"online_players": 0, "max_players": 20}
        mock_player_list = []

        with patch('services.rcon_service.rcon_service.get_player_count', return_value=mock_player_count), \
             patch('services.rcon_service.rcon_service.get_online_players', return_value=mock_player_list):

            response = await client.get(
                f"/api/v1/console/{test_server.id}/players",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["online_players"] == 0
            assert data["players"] == []

    async def test_get_players_rcon_failure(self, client, test_server, test_db, admin_token):
        """Test getting players when RCON fails."""
        test_server.status = ServerStatus.RUNNING
        test_db.add(test_server)
        await test_db.commit()

        with patch('services.rcon_service.rcon_service.get_player_count',
                   side_effect=Exception("RCON error")), \
             patch('services.rcon_service.rcon_service.get_online_players',
                   side_effect=Exception("RCON error")):

            response = await client.get(
                f"/api/v1/console/{test_server.id}/players",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            # Should return empty list with default values
            assert response.status_code == 200
            data = response.json()
            assert data["online_players"] == 0
            assert data["max_players"] == 20
            assert data["players"] == []

    async def test_get_players_server_not_found(self, client, admin_token):
        """Test getting players with non-existent server."""
        response = await client.get(
            "/api/v1/console/99999/players",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404

    async def test_get_players_no_auth(self, client, test_server):
        """Test getting players without authentication."""
        response = await client.get(
            f"/api/v1/console/{test_server.id}/players"
        )

        # HTTPBearer returns 403 when credentials are missing (not 401)
        assert response.status_code == 403
