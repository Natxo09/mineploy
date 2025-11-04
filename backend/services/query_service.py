"""
Query Protocol service for Minecraft server statistics.

This service uses Minecraft's native Query Protocol instead of RCON
to fetch server statistics without generating log spam.
"""

from typing import Dict, Any, List, Optional
from mcstatus import JavaServer


class QueryError(Exception):
    """Custom exception for Query Protocol errors."""
    pass


class MinecraftQueryService:
    """
    Service for querying Minecraft servers using Query Protocol.

    Query Protocol advantages over RCON for stats:
    - No authentication required (no password)
    - No log spam in server console or latest.log
    - Lightweight (UDP-based instead of TCP)
    - Native Minecraft protocol (built-in)

    Limitations:
    - Cannot execute commands (use RCON for that)
    - Cannot get TPS (use RCON for Paper/Spigot)
    - Requires enable-query=true in server.properties
    """

    def __init__(self):
        """Initialize Query service."""
        pass

    async def get_player_count(
        self,
        host: str,
        port: int,
        timeout: float = 5.0
    ) -> Dict[str, int]:
        """
        Get basic player count statistics using Query Protocol.

        Args:
            host: Server host (container name or IP)
            port: Query port (default: same as server port, usually 25565)
            timeout: Query timeout in seconds

        Returns:
            Dict with online_players and max_players:
            {
                "online_players": 3,
                "max_players": 20
            }

        Raises:
            QueryError: If query fails (server down, query disabled, timeout)
        """
        try:
            # Lookup server with query support
            server = JavaServer.lookup(f"{host}:{port}", timeout=timeout)

            # Perform query request
            query = await server.async_query()

            return {
                "online_players": len(query.players.names),
                "max_players": query.players.max,
            }
        except Exception as e:
            error_msg = f"Query failed for {host}:{port}: {str(e)}"
            print(f"⚠️  {error_msg}")
            raise QueryError(error_msg) from e

    async def get_full_stats(
        self,
        host: str,
        port: int,
        timeout: float = 5.0
    ) -> Dict[str, Any]:
        """
        Get full server statistics including player list.

        Args:
            host: Server host (container name or IP)
            port: Query port (default: same as server port)
            timeout: Query timeout in seconds

        Returns:
            Dict with comprehensive server info:
            {
                "online_players": 3,
                "max_players": 20,
                "players": ["Steve", "Alex", "Herobrine"],
                "motd": "My Minecraft Server",
                "map": "world",
                "game_type": "SMP",
                "version": "1.21.3",
                "plugins": []  # Only if running Bukkit/Spigot/Paper
            }

        Raises:
            QueryError: If query fails
        """
        try:
            server = JavaServer.lookup(f"{host}:{port}", timeout=timeout)
            query = await server.async_query()

            # Extract plugin info if available (Bukkit/Spigot/Paper)
            plugins = []
            if hasattr(query.software, 'plugins'):
                plugins = query.software.plugins

            return {
                "online_players": len(query.players.names),
                "max_players": query.players.max,
                "players": list(query.players.names),  # Convert from tuple to list
                "motd": query.motd,
                "map": query.map,
                "game_type": query.game_type,
                "version": query.software.version,
                "plugins": plugins,
            }
        except Exception as e:
            error_msg = f"Query failed for {host}:{port}: {str(e)}"
            print(f"⚠️  {error_msg}")
            raise QueryError(error_msg) from e

    async def test_connection(
        self,
        host: str,
        port: int,
        timeout: float = 5.0
    ) -> bool:
        """
        Test if Query Protocol is available and responding.

        Args:
            host: Server host
            port: Query port
            timeout: Connection timeout in seconds

        Returns:
            True if query is available, False otherwise
        """
        try:
            await self.get_player_count(host, port, timeout)
            return True
        except QueryError:
            return False


# Singleton instance for dependency injection
query_service = MinecraftQueryService()
