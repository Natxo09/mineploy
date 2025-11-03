"""
Tests for RCON service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from mcrcon import MCRconException

from services.rcon_service import RconService


@pytest.fixture
def rcon_service():
    """Create RCON service instance."""
    return RconService()


@pytest.mark.asyncio
class TestRconService:
    """Test RCON service functionality."""

    async def test_execute_command_success(self, rcon_service):
        """Test successful command execution."""
        mock_response = "Command executed successfully"

        with patch.object(rcon_service, '_execute_command_sync', return_value=mock_response):
            response = await rcon_service.execute_command(
                host="localhost",
                port=25575,
                password="test_password",
                command="list"
            )

            assert response == mock_response

    async def test_execute_command_with_timeout(self, rcon_service):
        """Test command execution with custom timeout."""
        mock_response = "Players online"

        with patch.object(rcon_service, '_execute_command_sync', return_value=mock_response) as mock_exec:
            await rcon_service.execute_command(
                host="localhost",
                port=25575,
                password="test_password",
                command="list",
                timeout=5
            )

            # Verify timeout was passed
            mock_exec.assert_called_once()
            assert mock_exec.call_args[0][4] == 5  # timeout argument

    async def test_get_player_count_success(self, rcon_service):
        """Test getting player count via RCON."""
        mock_response = "There are 5 of a max of 20 players online: Player1, Player2, Player3, Player4, Player5"

        with patch.object(rcon_service, 'execute_command', return_value=mock_response):
            result = await rcon_service.get_player_count(
                host="localhost",
                port=25575,
                password="test_password"
            )

            assert result == {"online_players": 5, "max_players": 20}

    async def test_get_player_count_no_players(self, rcon_service):
        """Test getting player count when no players online."""
        mock_response = "There are 0 of a max of 20 players online:"

        with patch.object(rcon_service, 'execute_command', return_value=mock_response):
            result = await rcon_service.get_player_count(
                host="localhost",
                port=25575,
                password="test_password"
            )

            assert result == {"online_players": 0, "max_players": 20}

    async def test_get_player_count_rcon_failure(self, rcon_service):
        """Test player count when RCON fails."""
        with patch.object(rcon_service, 'execute_command', side_effect=MCRconException("Connection failed")):
            result = await rcon_service.get_player_count(
                host="localhost",
                port=25575,
                password="test_password"
            )

            # Should return default values
            assert result == {"online_players": 0, "max_players": 20}

    async def test_get_online_players_success(self, rcon_service):
        """Test getting list of online players."""
        mock_response = "There are 3 of a max of 20 players online: Alice, Bob, Charlie"

        with patch.object(rcon_service, 'execute_command', return_value=mock_response):
            result = await rcon_service.get_online_players(
                host="localhost",
                port=25575,
                password="test_password"
            )

            assert result == ["Alice", "Bob", "Charlie"]

    async def test_get_online_players_no_players(self, rcon_service):
        """Test getting empty player list."""
        mock_response = "There are 0 of a max of 20 players online:"

        with patch.object(rcon_service, 'execute_command', return_value=mock_response):
            result = await rcon_service.get_online_players(
                host="localhost",
                port=25575,
                password="test_password"
            )

            assert result == []

    async def test_get_online_players_rcon_failure(self, rcon_service):
        """Test player list when RCON fails."""
        with patch.object(rcon_service, 'execute_command', side_effect=MCRconException("Connection failed")):
            result = await rcon_service.get_online_players(
                host="localhost",
                port=25575,
                password="test_password"
            )

            assert result == []

    async def test_get_tps_success(self, rcon_service):
        """Test getting TPS from Paper/Spigot server."""
        mock_response = "TPS from last 1m, 5m, 15m: 20.0, 19.8, 19.9"

        with patch.object(rcon_service, 'execute_command', return_value=mock_response):
            result = await rcon_service.get_tps(
                host="localhost",
                port=25575,
                password="test_password"
            )

            assert result == 20.0

    async def test_get_tps_not_available(self, rcon_service):
        """Test TPS when command not available (vanilla)."""
        with patch.object(rcon_service, 'execute_command', side_effect=MCRconException("Unknown command")):
            result = await rcon_service.get_tps(
                host="localhost",
                port=25575,
                password="test_password"
            )

            assert result is None

    async def test_test_connection_success(self, rcon_service):
        """Test successful RCON connection test."""
        mock_response = "There are 0 of a max of 20 players online:"

        with patch.object(rcon_service, 'execute_command', return_value=mock_response):
            success, error = await rcon_service.test_connection(
                host="localhost",
                port=25575,
                password="test_password"
            )

            assert success is True
            assert error is None

    async def test_test_connection_failure(self, rcon_service):
        """Test failed RCON connection test."""
        with patch.object(rcon_service, 'execute_command', side_effect=MCRconException("Connection refused")):
            success, error = await rcon_service.test_connection(
                host="localhost",
                port=25575,
                password="wrong_password"
            )

            assert success is False
            assert "Connection refused" in error

    async def test_send_message_success(self, rcon_service):
        """Test sending message to server."""
        with patch.object(rcon_service, 'execute_command', return_value=""):
            result = await rcon_service.send_message(
                host="localhost",
                port=25575,
                password="test_password",
                message="Hello, players!"
            )

            assert result is True

    async def test_send_message_failure(self, rcon_service):
        """Test send message when RCON fails."""
        with patch.object(rcon_service, 'execute_command', side_effect=MCRconException("Connection failed")):
            result = await rcon_service.send_message(
                host="localhost",
                port=25575,
                password="test_password",
                message="Hello, players!"
            )

            assert result is False

    async def test_stop_server_success(self, rcon_service):
        """Test stopping server via RCON."""
        with patch.object(rcon_service, 'execute_command', return_value="Stopping server..."):
            result = await rcon_service.stop_server(
                host="localhost",
                port=25575,
                password="test_password"
            )

            assert result is True

    async def test_stop_server_failure(self, rcon_service):
        """Test stop server when RCON fails."""
        with patch.object(rcon_service, 'execute_command', side_effect=MCRconException("Connection failed")):
            result = await rcon_service.stop_server(
                host="localhost",
                port=25575,
                password="test_password"
            )

            assert result is False
