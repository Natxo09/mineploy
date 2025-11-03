"""
Docker service for managing Minecraft server containers.
"""

import aiodocker
from aiodocker.containers import DockerContainer
from aiodocker.exceptions import DockerError
from typing import Optional, Dict, Any, Callable
import secrets
import string
import json

from core.config import settings
from models.server import ServerType, ServerStatus


class DockerService:
    """Service for Docker container management."""

    def __init__(self):
        """Initialize Docker client."""
        self.docker: Optional[aiodocker.Docker] = None

    async def connect(self):
        """Connect to Docker daemon."""
        if not self.docker:
            self.docker = aiodocker.Docker(url=f"unix://{settings.docker_socket}")

    async def close(self):
        """Close Docker connection."""
        if self.docker:
            await self.docker.close()
            self.docker = None

    def _generate_rcon_password(self) -> str:
        """Generate a secure random RCON password."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))

    def _get_server_image_config(self, server_type: ServerType) -> str:
        """Get the server type configuration for itzg/minecraft-server."""
        type_map = {
            ServerType.VANILLA: "VANILLA",
            ServerType.PAPER: "PAPER",
            ServerType.SPIGOT: "SPIGOT",
            ServerType.FABRIC: "FABRIC",
            ServerType.FORGE: "FORGE",
            ServerType.NEOFORGE: "NEOFORGE",
            ServerType.PURPUR: "PURPUR",
        }
        return type_map.get(server_type, "VANILLA")

    async def pull_image_with_progress(
        self,
        image: str = "itzg/minecraft-server:latest",
        on_progress: Optional[Callable[[dict], None]] = None,
    ) -> bool:
        """
        Pull a Docker image with progress tracking.

        Args:
            image: Docker image to pull
            on_progress: Callback function to receive progress updates

        Returns:
            True if pull was successful

        Raises:
            DockerError: If pull fails
        """
        await self.connect()

        try:
            print(f"📦 Pulling Docker image: {image}")

            # Pull image and stream progress
            async for line in self.docker.images.pull(image, stream=True):
                if on_progress:
                    # Parse the JSON line
                    try:
                        progress_data = json.loads(line)
                        on_progress(progress_data)
                    except json.JSONDecodeError:
                        pass

            print(f"✅ Successfully pulled image: {image}")
            return True

        except DockerError as e:
            print(f"❌ Failed to pull image {image}: {str(e)}")
            raise DockerError(f"Failed to pull image: {str(e)}", {"message": str(e)})

    async def create_container(
        self,
        container_name: str,
        server_type: ServerType,
        version: str,
        port: int,
        rcon_port: int,
        rcon_password: str,
        memory_mb: int = 2048,
    ) -> tuple[str, Dict[str, Any]]:
        """
        Create a Minecraft server container.

        Args:
            container_name: Unique container name
            server_type: Type of Minecraft server
            version: Minecraft version
            port: Server port
            rcon_port: RCON port
            rcon_password: RCON password
            memory_mb: Memory limit in MB

        Returns:
            Tuple of (container_id, container_info)

        Raises:
            DockerError: If container creation fails
        """
        await self.connect()

        # Prepare environment variables
        env = [
            "EULA=TRUE",
            f"TYPE={self._get_server_image_config(server_type)}",
            f"VERSION={version}",
            f"MEMORY={memory_mb}M",
            "ENABLE_RCON=TRUE",
            f"RCON_PORT={rcon_port}",
            f"RCON_PASSWORD={rcon_password}",
            "ONLINE_MODE=TRUE",
            "SERVER_PORT=25565",  # Internal port (always 25565 inside container)
        ]

        # Container configuration
        config = {
            "Image": "itzg/minecraft-server:latest",
            "Hostname": container_name,
            "Env": env,
            "ExposedPorts": {
                f"{25565}/tcp": {},  # Minecraft port
                f"{rcon_port}/tcp": {},  # RCON port
            },
            "HostConfig": {
                "PortBindings": {
                    f"{25565}/tcp": [{"HostPort": str(port)}],
                    f"{rcon_port}/tcp": [{"HostPort": str(rcon_port)}],
                },
                "Memory": memory_mb * 1024 * 1024,  # Convert MB to bytes
                "NetworkMode": "minecraft_network",  # Use dedicated network
                "RestartPolicy": {"Name": "unless-stopped"},
            },
            "Labels": {
                "mineploy.managed": "true",
                "mineploy.server_type": server_type.value,
                "mineploy.version": version,
            },
        }

        # Create container
        try:
            container = await self.docker.containers.create(
                name=container_name,
                config=config
            )

            # Get container info
            container_info = await container.show()

            return container_info["Id"], container_info

        except DockerError as e:
            raise DockerError(f"Failed to create container: {str(e)}", {"message": str(e)})

    async def start_container(self, container_id: str) -> bool:
        """
        Start a container.

        Args:
            container_id: Container ID

        Returns:
            True if started successfully

        Raises:
            DockerError: If start fails
        """
        await self.connect()

        try:
            container = self.docker.containers.container(container_id)
            await container.start()
            return True
        except DockerError as e:
            raise DockerError(f"Failed to start container: {str(e)}", {"message": str(e)})

    async def stop_container(self, container_id: str, timeout: int = 30) -> bool:
        """
        Stop a container gracefully.

        Args:
            container_id: Container ID
            timeout: Timeout in seconds before force kill

        Returns:
            True if stopped successfully

        Raises:
            DockerError: If stop fails
        """
        await self.connect()

        try:
            container = self.docker.containers.container(container_id)
            await container.stop(timeout=timeout)
            return True
        except DockerError as e:
            raise DockerError(f"Failed to stop container: {str(e)}", {"message": str(e)})

    async def restart_container(self, container_id: str, timeout: int = 30) -> bool:
        """
        Restart a container.

        Args:
            container_id: Container ID
            timeout: Timeout in seconds

        Returns:
            True if restarted successfully

        Raises:
            DockerError: If restart fails
        """
        await self.connect()

        try:
            container = self.docker.containers.container(container_id)
            await container.restart(timeout=timeout)
            return True
        except DockerError as e:
            raise DockerError(f"Failed to restart container: {str(e)}", {"message": str(e)})

    async def delete_container(self, container_id: str, force: bool = False) -> bool:
        """
        Delete a container.

        Args:
            container_id: Container ID
            force: Force removal even if running

        Returns:
            True if deleted successfully

        Raises:
            DockerError: If deletion fails
        """
        await self.connect()

        try:
            container = self.docker.containers.container(container_id)

            # Stop first if running and force is False
            if not force:
                try:
                    await self.stop_container(container_id)
                except Exception:
                    pass  # Container might already be stopped

            await container.delete(force=force)
            return True
        except DockerError as e:
            raise DockerError(f"Failed to delete container: {str(e)}", {"message": str(e)})

    async def get_container_status(self, container_id: str) -> ServerStatus:
        """
        Get container status.

        Args:
            container_id: Container ID

        Returns:
            ServerStatus enum value

        Raises:
            DockerError: If status check fails
        """
        await self.connect()

        try:
            container = self.docker.containers.container(container_id)
            info = await container.show()

            state = info.get("State", {})
            status = state.get("Status", "").lower()

            # Map Docker status to ServerStatus
            if status == "running":
                return ServerStatus.RUNNING
            elif status == "exited" or status == "created":
                return ServerStatus.STOPPED
            elif status == "restarting":
                return ServerStatus.STARTING
            elif status == "dead":
                return ServerStatus.ERROR
            else:
                return ServerStatus.STOPPED

        except DockerError:
            return ServerStatus.ERROR

    async def get_container_stats(self, container_id: str) -> Optional[Dict[str, Any]]:
        """
        Get container resource stats.

        Args:
            container_id: Container ID

        Returns:
            Dictionary with CPU and memory stats, or None if unavailable

        Raises:
            DockerError: If stats retrieval fails
        """
        await self.connect()

        try:
            container = self.docker.containers.container(container_id)
            stats = await container.stats(stream=False)

            # Extract relevant stats
            cpu_stats = stats.get("cpu_stats", {})
            memory_stats = stats.get("memory_stats", {})

            # Calculate CPU percentage
            cpu_delta = cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
            system_delta = cpu_stats.get("system_cpu_usage", 0)
            cpu_count = cpu_stats.get("online_cpus", 1)

            cpu_percent = 0.0
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0

            # Get memory stats
            memory_usage = memory_stats.get("usage", 0)
            memory_limit = memory_stats.get("limit", 0)

            return {
                "cpu_percent": round(cpu_percent, 2),
                "memory_usage_mb": round(memory_usage / (1024 * 1024), 2),
                "memory_limit_mb": round(memory_limit / (1024 * 1024), 2),
                "memory_percent": round((memory_usage / memory_limit * 100) if memory_limit > 0 else 0, 2),
            }

        except DockerError:
            return None

    async def container_exists(self, container_name: str) -> bool:
        """
        Check if a container exists.

        Args:
            container_name: Container name

        Returns:
            True if container exists
        """
        await self.connect()

        try:
            containers = await self.docker.containers.list(all=True)
            for container in containers:
                info = await container.show()
                names = info.get("Name", "")
                # Docker may include '/' prefix in name
                if names.lstrip("/") == container_name:
                    return True
            return False
        except DockerError:
            return False


# Global instance
docker_service = DockerService()
