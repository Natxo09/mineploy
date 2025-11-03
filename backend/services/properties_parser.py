"""
Service for reading and parsing Minecraft server.properties files.
"""

from typing import Dict, Optional, Any
import re


class PropertiesParser:
    """Parser for Minecraft server.properties files."""

    @staticmethod
    def parse(content: str) -> Dict[str, str]:
        """
        Parse server.properties content into a dictionary.

        Args:
            content: Raw content of server.properties file

        Returns:
            Dictionary of property key-value pairs
        """
        properties = {}

        for line in content.splitlines():
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Split on first = only
            if '=' in line:
                key, value = line.split('=', 1)
                properties[key.strip()] = value.strip()

        return properties

    @staticmethod
    def get_rcon_config(properties: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract RCON configuration from properties.

        Args:
            properties: Parsed properties dictionary

        Returns:
            Dict with rcon_enabled, rcon_port, and rcon_password
        """
        rcon_enabled = properties.get('enable-rcon', 'false').lower() == 'true'
        rcon_port = int(properties.get('rcon.port', '25575'))
        rcon_password = properties.get('rcon.password', '')

        return {
            'rcon_enabled': rcon_enabled,
            'rcon_port': rcon_port,
            'rcon_password': rcon_password
        }

    @staticmethod
    def get_server_config(properties: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract server configuration from properties.

        Args:
            properties: Parsed properties dictionary

        Returns:
            Dict with server settings
        """
        return {
            'server_port': int(properties.get('server-port', '25565')),
            'max_players': int(properties.get('max-players', '20')),
            'difficulty': properties.get('difficulty', 'normal'),
            'gamemode': properties.get('gamemode', 'survival'),
            'pvp': properties.get('pvp', 'true').lower() == 'true',
            'online_mode': properties.get('online-mode', 'true').lower() == 'true',
            'motd': properties.get('motd', 'A Minecraft Server'),
            'level_name': properties.get('level-name', 'world'),
            'seed': properties.get('level-seed', ''),
            'view_distance': int(properties.get('view-distance', '10')),
            'spawn_protection': int(properties.get('spawn-protection', '16')),
        }

    @staticmethod
    def validate_rcon_config(rcon_config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate RCON configuration.

        Args:
            rcon_config: RCON configuration dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not rcon_config.get('rcon_enabled'):
            return (False, "RCON is not enabled in server.properties")

        if not rcon_config.get('rcon_password'):
            return (False, "RCON password is empty in server.properties")

        rcon_port = rcon_config.get('rcon_port', 0)
        if not (1024 <= rcon_port <= 65535):
            return (False, f"Invalid RCON port: {rcon_port}")

        return (True, None)


# Global instance
properties_parser = PropertiesParser()
