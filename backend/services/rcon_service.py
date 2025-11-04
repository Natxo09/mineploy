"""
RCON service for Minecraft server communication.
"""

from typing import Optional, Dict, Any
import re

from services.async_rcon import AsyncRconClient, RconError


class RconService:
    """Service for RCON communication with Minecraft servers."""

    def __init__(self):
        """Initialize RCON service."""
        pass

    async def execute_command(
        self,
        host: str,
        port: int,
        password: str,
        command: str,
        timeout: int = 10,
    ) -> str:
        """
        Execute a command via RCON.

        Args:
            host: Server host
            port: RCON port
            password: RCON password
            command: Command to execute
            timeout: Connection timeout in seconds

        Returns:
            Command response from server

        Raises:
            RconError: If RCON connection fails
        """
        try:
            async with AsyncRconClient(host, port, password, timeout=float(timeout)) as client:
                response = await client.send_command(command)
                return response
        except Exception as e:
            raise

    async def get_player_count(
        self, host: str, port: int, password: str
    ) -> Dict[str, int]:
        """
        Get online player count via RCON.

        Args:
            host: Server host
            port: RCON port
            password: RCON password

        Returns:
            Dict with online_players and max_players

        Raises:
            MCRconException: If RCON connection fails
        """
        try:
            response = await self.execute_command(host, port, password, "list")

            # Parse response like "There are 3 of a max of 20 players online: Player1, Player2, Player3"
            match = re.search(r"There are (\d+) of a max of (\d+)", response)
            if match:
                online = int(match.group(1))
                max_players = int(match.group(2))
                return {"online_players": online, "max_players": max_players}

            # Fallback parsing
            return {"online_players": 0, "max_players": 20}

        except RconError as e:
            print(f"⚠️  Failed to get player count via RCON: {e}")
            return {"online_players": 0, "max_players": 20}
        except Exception as e:
            print(f"⚠️  Unexpected error getting player count: {e}")
            return {"online_players": 0, "max_players": 20}

    async def get_online_players(
        self, host: str, port: int, password: str
    ) -> list[str]:
        """
        Get list of online players via RCON.

        Args:
            host: Server host
            port: RCON port
            password: RCON password

        Returns:
            List of player names

        Raises:
            MCRconException: If RCON connection fails
        """
        try:
            response = await self.execute_command(host, port, password, "list")

            # Parse response to extract player names
            # Format: "There are X of a max of Y players online: Player1, Player2, Player3"
            if ":" in response:
                players_str = response.split(":", 1)[1].strip()
                if players_str:
                    players = [p.strip() for p in players_str.split(",") if p.strip()]
                    return players

            return []

        except RconError as e:
            print(f"⚠️  Failed to get online players via RCON: {e}")
            return []
        except Exception as e:
            print(f"⚠️  Unexpected error getting online players: {e}")
            return []

    async def get_tps(self, host: str, port: int, password: str) -> Optional[float]:
        """
        Get server TPS (Ticks Per Second) via RCON.
        Note: Only works on Paper/Spigot/Purpur servers.

        Args:
            host: Server host
            port: RCON port
            password: RCON password

        Returns:
            TPS value or None if not available

        Raises:
            MCRconException: If RCON connection fails
        """
        try:
            response = await self.execute_command(host, port, password, "tps")

            # Parse TPS from response
            # Example: "TPS from last 1m, 5m, 15m: 20.0, 20.0, 20.0"
            match = re.search(r"(\d+\.\d+)", response)
            if match:
                return float(match.group(1))

            return None

        except (RconError, Exception):
            # Command might not be available on vanilla servers
            return None

    async def test_connection(
        self, host: str, port: int, password: str
    ) -> tuple[bool, Optional[str]]:
        """
        Test RCON connection to a server.

        Args:
            host: Server host
            port: RCON port
            password: RCON password

        Returns:
            Tuple of (success, error_message)
        """
        try:
            await self.execute_command(host, port, password, "list", timeout=5)
            return (True, None)
        except RconError as e:
            return (False, str(e))
        except Exception as e:
            return (False, f"Unexpected error: {str(e)}")

    async def send_message(
        self, host: str, port: int, password: str, message: str
    ) -> bool:
        """
        Send a message to all players on the server.

        Args:
            host: Server host
            port: RCON port
            password: RCON password
            message: Message to send

        Returns:
            True if message was sent successfully

        Raises:
            MCRconException: If RCON connection fails
        """
        try:
            await self.execute_command(
                host, port, password, f'say {message}'
            )
            return True
        except (RconError, Exception) as e:
            print(f"⚠️  Failed to send message via RCON: {e}")
            return False

    async def stop_server(self, host: str, port: int, password: str) -> bool:
        """
        Stop the server gracefully via RCON.

        Args:
            host: Server host
            port: RCON port
            password: RCON password

        Returns:
            True if stop command was sent successfully

        Raises:
            MCRconException: If RCON connection fails
        """
        try:
            await self.execute_command(host, port, password, "stop")
            return True
        except (RconError, Exception) as e:
            print(f"⚠️  Failed to stop server via RCON: {e}")
            return False


# Global instance
rcon_service = RconService()
