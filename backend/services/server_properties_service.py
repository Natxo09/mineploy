"""
Service for managing Minecraft server.properties configuration.
"""

import aiodocker
from aiodocker.exceptions import DockerError
from typing import Dict, Any, Optional
import tarfile
import io

from core.config import settings
from services.properties_parser import PropertiesParser
from schemas.properties import ServerPropertiesResponse, ServerPropertiesUpdate


class ServerPropertiesService:
    """Service for managing server.properties files in Docker containers."""

    def __init__(self):
        """Initialize Docker client."""
        self.docker: Optional[aiodocker.Docker] = None
        self.parser = PropertiesParser()

    async def connect(self):
        """Connect to Docker daemon."""
        if not self.docker:
            self.docker = aiodocker.Docker(url=f"unix://{settings.docker_socket}")

    async def close(self):
        """Close Docker connection."""
        if self.docker:
            await self.docker.close()
            self.docker = None

    async def read_properties_file(self, container_id: str) -> str:
        """
        Read server.properties file from container.

        Args:
            container_id: Docker container ID

        Returns:
            Content of server.properties file

        Raises:
            DockerError: If file cannot be read
            FileNotFoundError: If file doesn't exist
        """
        await self.connect()

        try:
            container = self.docker.containers.container(container_id)

            # Get file from container as tar archive
            tar_obj = await container.get_archive("/data/server.properties")

            # Check if it's already a TarFile object or if we need to open it
            if isinstance(tar_obj, tarfile.TarFile):
                # Already a TarFile, use directly
                tar_file = tar_obj
            else:
                # It's bytes or a stream, need to open it
                if hasattr(tar_obj, 'read'):
                    tar_data = tar_obj.read()
                else:
                    tar_data = tar_obj
                tar_file = tarfile.open(fileobj=io.BytesIO(tar_data))

            # Extract file from tar
            file_obj = tar_file.extractfile("server.properties")

            if file_obj is None:
                raise FileNotFoundError("server.properties not found in container")

            content = file_obj.read().decode('utf-8')
            return content

        except DockerError as e:
            if e.status == 404:
                raise FileNotFoundError("server.properties not found in container")
            raise DockerError(e.status, {"message": f"Failed to read server.properties: {str(e)}"})

    async def write_properties_file(self, container_id: str, content: str) -> bool:
        """
        Write server.properties file to container.

        Args:
            container_id: Docker container ID
            content: Content to write

        Returns:
            True if write was successful

        Raises:
            DockerError: If file cannot be written
        """
        await self.connect()

        try:
            container = self.docker.containers.container(container_id)

            # Create tar archive in memory
            tar_buffer = io.BytesIO()
            tar = tarfile.TarFile(fileobj=tar_buffer, mode='w')

            # Add file to tar
            file_data = content.encode('utf-8')
            tarinfo = tarfile.TarInfo(name='server.properties')
            tarinfo.size = len(file_data)
            tarinfo.mode = 0o644

            tar.addfile(tarinfo, io.BytesIO(file_data))
            tar.close()

            # Upload tar to container
            tar_buffer.seek(0)
            await container.put_archive("/data", tar_buffer.read())

            return True

        except DockerError as e:
            raise DockerError(e.status, {"message": f"Failed to write server.properties: {str(e)}"})

    def _parse_to_response(self, properties: Dict[str, str]) -> ServerPropertiesResponse:
        """
        Parse properties dictionary to ServerPropertiesResponse schema.

        Args:
            properties: Parsed properties dictionary

        Returns:
            ServerPropertiesResponse object
        """
        def get_bool(key: str, default: bool = False) -> bool:
            return properties.get(key, str(default)).lower() == 'true'

        def get_int(key: str, default: int = 0) -> int:
            try:
                return int(properties.get(key, str(default)))
            except ValueError:
                return default

        def get_str(key: str, default: str = '') -> str:
            return properties.get(key, default)

        return ServerPropertiesResponse(
            # Server settings
            motd=get_str('motd', 'A Minecraft Server'),
            max_players=get_int('max-players', 20),
            server_port=get_int('server-port', 25565),

            # Gameplay settings
            gamemode=get_str('gamemode', 'survival'),
            difficulty=get_str('difficulty', 'normal'),
            hardcore=get_bool('hardcore', False),
            pvp=get_bool('pvp', True),

            # World settings
            level_name=get_str('level-name', 'world'),
            level_seed=get_str('level-seed', ''),
            level_type=get_str('level-type', 'default'),
            generate_structures=get_bool('generate-structures', True),
            spawn_monsters=get_bool('spawn-monsters', True),
            spawn_animals=get_bool('spawn-animals', True),
            spawn_npcs=get_bool('spawn-npcs', True),

            # Performance settings
            view_distance=get_int('view-distance', 10),
            simulation_distance=get_int('simulation-distance', 10),
            max_tick_time=get_int('max-tick-time', 60000),

            # Network settings
            online_mode=get_bool('online-mode', True),
            enable_status=get_bool('enable-status', True),
            allow_flight=get_bool('allow-flight', False),
            max_world_size=get_int('max-world-size', 29999984),

            # Spawn settings
            spawn_protection=get_int('spawn-protection', 16),
            force_gamemode=get_bool('force-gamemode', False),

            # Other settings
            white_list=get_bool('white-list', False),
            enforce_whitelist=get_bool('enforce-whitelist', False),
            resource_pack=get_str('resource-pack', ''),
            resource_pack_prompt=get_str('resource-pack-prompt', ''),
            require_resource_pack=get_bool('require-resource-pack', False),
            enable_command_block=get_bool('enable-command-block', False),
            function_permission_level=get_int('function-permission-level', 2),
            op_permission_level=get_int('op-permission-level', 4),

            # RCON settings
            enable_rcon=get_bool('enable-rcon', False),
            rcon_port=get_int('rcon.port', 25575),
            rcon_password=get_str('rcon.password', ''),

            # Query settings
            enable_query=get_bool('enable-query', False),
            query_port=get_int('query.port', 25565),
        )

    def _update_dict_to_properties_dict(self, update: ServerPropertiesUpdate) -> Dict[str, Any]:
        """
        Convert ServerPropertiesUpdate to properties dictionary format.

        Args:
            update: ServerPropertiesUpdate object

        Returns:
            Dictionary with property keys in server.properties format
        """
        properties = {}

        # Map schema fields to server.properties keys
        mapping = {
            'motd': 'motd',
            'max_players': 'max-players',
            'gamemode': 'gamemode',
            'difficulty': 'difficulty',
            'hardcore': 'hardcore',
            'pvp': 'pvp',
            'level_seed': 'level-seed',
            'level_type': 'level-type',
            'generate_structures': 'generate-structures',
            'spawn_monsters': 'spawn-monsters',
            'spawn_animals': 'spawn-animals',
            'spawn_npcs': 'spawn-npcs',
            'view_distance': 'view-distance',
            'simulation_distance': 'simulation-distance',
            'max_tick_time': 'max-tick-time',
            'online_mode': 'online-mode',
            'enable_status': 'enable-status',
            'allow_flight': 'allow-flight',
            'max_world_size': 'max-world-size',
            'spawn_protection': 'spawn-protection',
            'force_gamemode': 'force-gamemode',
            'white_list': 'white-list',
            'enforce_whitelist': 'enforce-whitelist',
            'resource_pack': 'resource-pack',
            'resource_pack_prompt': 'resource-pack-prompt',
            'require_resource_pack': 'require-resource-pack',
            'enable_command_block': 'enable-command-block',
            'function_permission_level': 'function-permission-level',
            'op_permission_level': 'op-permission-level',
            'enable_query': 'enable-query',
        }

        # Convert update object to dict and filter None values
        update_dict = update.model_dump(exclude_none=True)

        for schema_key, prop_key in mapping.items():
            if schema_key in update_dict:
                properties[prop_key] = update_dict[schema_key]

        return properties

    async def get_properties(self, container_id: str) -> ServerPropertiesResponse:
        """
        Get server properties from container.

        Args:
            container_id: Docker container ID

        Returns:
            ServerPropertiesResponse object

        Raises:
            DockerError: If properties cannot be read
            FileNotFoundError: If file doesn't exist
        """
        content = await self.read_properties_file(container_id)
        properties = self.parser.parse(content)
        return self._parse_to_response(properties)

    async def update_properties(
        self,
        container_id: str,
        updates: ServerPropertiesUpdate
    ) -> ServerPropertiesResponse:
        """
        Update server properties in container.

        Args:
            container_id: Docker container ID
            updates: Properties to update

        Returns:
            Updated ServerPropertiesResponse object

        Raises:
            DockerError: If properties cannot be updated
            FileNotFoundError: If file doesn't exist
        """
        # Read current properties
        current_content = await self.read_properties_file(container_id)

        # Convert update to properties dict
        update_dict = self._update_dict_to_properties_dict(updates)

        # Update properties
        new_content = self.parser.update_properties(current_content, update_dict)

        # Write back to container
        await self.write_properties_file(container_id, new_content)

        # Parse and return updated properties
        properties = self.parser.parse(new_content)
        return self._parse_to_response(properties)


# Global instance
server_properties_service = ServerPropertiesService()
