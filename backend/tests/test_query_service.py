"""
Tests for Query Protocol service.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from services.query_service import MinecraftQueryService, QueryError


@pytest.fixture
def query_service():
    """Create Query service instance."""
    return MinecraftQueryService()


@pytest.mark.asyncio
class TestQueryService:
    """Test Query Protocol service functionality."""

    async def test_get_player_count_success(self, query_service):
        """Test successfully getting player count via Query Protocol."""
        # Mock JavaServer and query response
        mock_query = Mock()
        mock_query.players.names = ["Player1", "Player2", "Player3"]
        mock_query.players.max = 20

        mock_server = AsyncMock()
        mock_server.async_query.return_value = mock_query

        with patch('services.query_service.JavaServer.lookup', return_value=mock_server):
            result = await query_service.get_player_count(
                host="minecraft_server",
                port=25565
            )

            assert result == {"online_players": 3, "max_players": 20}
            mock_server.async_query.assert_called_once()

    async def test_get_player_count_no_players(self, query_service):
        """Test getting player count when no players online."""
        mock_query = Mock()
        mock_query.players.names = []
        mock_query.players.max = 20

        mock_server = AsyncMock()
        mock_server.async_query.return_value = mock_query

        with patch('services.query_service.JavaServer.lookup', return_value=mock_server):
            result = await query_service.get_player_count(
                host="minecraft_server",
                port=25565
            )

            assert result == {"online_players": 0, "max_players": 20}

    async def test_get_player_count_timeout(self, query_service):
        """Test Query Protocol timeout."""
        mock_server = AsyncMock()
        mock_server.async_query.side_effect = TimeoutError("Query timeout")

        with patch('services.query_service.JavaServer.lookup', return_value=mock_server):
            with pytest.raises(QueryError, match="Query failed"):
                await query_service.get_player_count(
                    host="minecraft_server",
                    port=25565,
                    timeout=2.0
                )

    async def test_get_full_stats_success(self, query_service):
        """Test getting full server statistics via Query Protocol."""
        # Mock query response with full stats
        mock_query = Mock()
        mock_query.players.names = ("Steve", "Alex")  # mcstatus returns tuple
        mock_query.players.max = 20
        mock_query.motd = "My Minecraft Server"
        mock_query.map = "world"
        mock_query.game_type = "SMP"
        mock_query.software.version = "1.21.3"
        mock_query.software.plugins = []

        mock_server = AsyncMock()
        mock_server.async_query.return_value = mock_query

        with patch('services.query_service.JavaServer.lookup', return_value=mock_server):
            result = await query_service.get_full_stats(
                host="minecraft_server",
                port=25565
            )

            assert result == {
                "online_players": 2,
                "max_players": 20,
                "players": ["Steve", "Alex"],  # Converted to list
                "motd": "My Minecraft Server",
                "map": "world",
                "game_type": "SMP",
                "version": "1.21.3",
                "plugins": []
            }

    async def test_get_full_stats_with_plugins(self, query_service):
        """Test getting full stats from server with plugins (Bukkit/Paper)."""
        mock_query = Mock()
        mock_query.players.names = ("Player1",)
        mock_query.players.max = 10
        mock_query.motd = "Modded Server"
        mock_query.map = "world"
        mock_query.game_type = "SMP"
        mock_query.software.version = "1.21.3-paper"
        mock_query.software.plugins = ["EssentialsX", "WorldEdit"]

        mock_server = AsyncMock()
        mock_server.async_query.return_value = mock_query

        with patch('services.query_service.JavaServer.lookup', return_value=mock_server):
            result = await query_service.get_full_stats(
                host="minecraft_server",
                port=25565
            )

            assert result["plugins"] == ["EssentialsX", "WorldEdit"]
            assert result["version"] == "1.21.3-paper"

    async def test_get_full_stats_query_disabled(self, query_service):
        """Test Query Protocol when server has query disabled."""
        mock_server = AsyncMock()
        mock_server.async_query.side_effect = Exception("Query is disabled on this server")

        with patch('services.query_service.JavaServer.lookup', return_value=mock_server):
            with pytest.raises(QueryError, match="Query failed"):
                await query_service.get_full_stats(
                    host="minecraft_server",
                    port=25565
                )

    async def test_test_connection_success(self, query_service):
        """Test successful Query Protocol connection test."""
        mock_query = Mock()
        mock_query.players.names = []
        mock_query.players.max = 20

        mock_server = AsyncMock()
        mock_server.async_query.return_value = mock_query

        with patch('services.query_service.JavaServer.lookup', return_value=mock_server):
            result = await query_service.test_connection(
                host="minecraft_server",
                port=25565
            )

            assert result is True

    async def test_test_connection_failure(self, query_service):
        """Test failed Query Protocol connection test."""
        mock_server = AsyncMock()
        mock_server.async_query.side_effect = Exception("Connection refused")

        with patch('services.query_service.JavaServer.lookup', return_value=mock_server):
            result = await query_service.test_connection(
                host="minecraft_server",
                port=25565
            )

            assert result is False

    async def test_custom_timeout(self, query_service):
        """Test Query Protocol with custom timeout."""
        mock_query = Mock()
        mock_query.players.names = []
        mock_query.players.max = 20

        mock_server = AsyncMock()
        mock_server.async_query.return_value = mock_query

        with patch('services.query_service.JavaServer.lookup', return_value=mock_server) as mock_lookup:
            await query_service.get_player_count(
                host="minecraft_server",
                port=25565,
                timeout=10.0
            )

            # Verify custom timeout was passed to JavaServer.lookup
            mock_lookup.assert_called_once_with("minecraft_server:25565", timeout=10.0)
