"""
Service for Docker cleanup operations and disk usage monitoring.
"""

import aiodocker
from aiodocker.exceptions import DockerError
from typing import Dict, Any, Optional
import asyncio

from core.config import settings


class DockerCleanupService:
    """Service for managing Docker cleanup and monitoring disk usage."""

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

    async def _run_docker_command(self, command: list[str]) -> tuple[str, str]:
        """
        Run a Docker CLI command and return stdout/stderr.

        Args:
            command: List of command arguments (e.g., ['docker', 'system', 'df'])

        Returns:
            Tuple of (stdout, stderr)

        Raises:
            RuntimeError: If command fails
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise RuntimeError(f"Command failed: {stderr.decode()}")

            return stdout.decode(), stderr.decode()

        except Exception as e:
            raise RuntimeError(f"Failed to execute Docker command: {str(e)}")

    def _parse_size_string(self, size_str: str) -> int:
        """
        Parse Docker size string to bytes.

        Args:
            size_str: Size string like "2.4GB", "156MB", "0B"

        Returns:
            Size in bytes
        """
        size_str = size_str.strip().upper()

        if size_str == "0B" or size_str == "0":
            return 0

        # Extract number and unit
        number = ""
        unit = ""
        for char in size_str:
            if char.isdigit() or char == ".":
                number += char
            else:
                unit += char

        try:
            value = float(number)
        except ValueError:
            return 0

        # Convert to bytes
        unit = unit.strip()
        multipliers = {
            "B": 1,
            "KB": 1024,
            "MB": 1024 ** 2,
            "GB": 1024 ** 3,
            "TB": 1024 ** 4,
        }

        return int(value * multipliers.get(unit, 1))

    def _format_bytes(self, bytes_size: int) -> str:
        """
        Format bytes to human-readable string.

        Args:
            bytes_size: Size in bytes

        Returns:
            Formatted string (e.g., "2.4 GB")
        """
        if bytes_size == 0:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0

        size = float(bytes_size)
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        return f"{size:.1f} {units[unit_index]}"

    async def get_disk_usage(self) -> Dict[str, Any]:
        """
        Get Docker disk usage statistics.

        Returns:
            Dictionary with disk usage information:
            {
                "images": {"size": bytes, "size_formatted": str, "count": int},
                "containers": {"size": bytes, "size_formatted": str, "count": int},
                "volumes": {"size": bytes, "size_formatted": str, "count": int},
                "build_cache": {"size": bytes, "size_formatted": str},
                "total": {"size": bytes, "size_formatted": str}
            }

        Raises:
            RuntimeError: If disk usage cannot be retrieved
        """
        await self.connect()

        try:
            # Get images
            images = await self.docker.images.list()
            images_size = sum(img.get("Size", 0) for img in images)
            images_count = len(images)

            # Get all containers (including stopped)
            containers = await self.docker.containers.list(all=True)
            containers_size = sum(
                c.get("SizeRw", 0) + c.get("SizeRootFs", 0)
                for c in containers
            )
            containers_count = len(containers)

            # Get volumes
            volumes_data = await self.docker.volumes.list()
            volumes = volumes_data.get("Volumes", []) if volumes_data else []

            # Calculate volumes size (note: UsageData may not be available in all Docker versions)
            volumes_size = 0
            for v in volumes:
                if isinstance(v, dict) and "UsageData" in v:
                    volumes_size += v.get("UsageData", {}).get("Size", 0)

            volumes_count = len(volumes)

            # Build cache size (not easily accessible via aiodocker, set to 0)
            build_cache_size = 0

            # Calculate total
            total_size = images_size + containers_size + volumes_size + build_cache_size

            return {
                "images": {
                    "size": images_size,
                    "size_formatted": self._format_bytes(images_size),
                    "count": images_count,
                },
                "containers": {
                    "size": containers_size,
                    "size_formatted": self._format_bytes(containers_size),
                    "count": containers_count,
                },
                "volumes": {
                    "size": volumes_size,
                    "size_formatted": self._format_bytes(volumes_size),
                    "count": volumes_count,
                },
                "build_cache": {
                    "size": build_cache_size,
                    "size_formatted": self._format_bytes(build_cache_size),
                },
                "total": {
                    "size": total_size,
                    "size_formatted": self._format_bytes(total_size),
                },
            }

        except DockerError as e:
            raise RuntimeError(f"Failed to get disk usage: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to get disk usage: {str(e)}")

    async def prune_images(self, all: bool = True) -> Dict[str, Any]:
        """
        Remove unused Docker images.

        Args:
            all: If True, remove all unused images. If False, only dangling images.

        Returns:
            Dictionary with pruning results:
            {
                "images_deleted": int,
                "space_reclaimed": int,
                "space_reclaimed_formatted": str
            }

        Raises:
            RuntimeError: If pruning fails
        """
        await self.connect()

        try:
            # Use aiodocker's prune API
            result = await self.docker.images.prune(filters={"dangling": ["false"]} if all else {})

            images_deleted = len(result.get("ImagesDeleted", []))
            space_reclaimed = result.get("SpaceReclaimed", 0)

            return {
                "images_deleted": images_deleted,
                "space_reclaimed": space_reclaimed,
                "space_reclaimed_formatted": self._format_bytes(space_reclaimed),
            }

        except DockerError as e:
            raise RuntimeError(f"Failed to prune images: {str(e)}")

    async def prune_containers(self) -> Dict[str, Any]:
        """
        Remove stopped containers.

        Returns:
            Dictionary with pruning results:
            {
                "containers_deleted": int,
                "space_reclaimed": int,
                "space_reclaimed_formatted": str
            }

        Raises:
            RuntimeError: If pruning fails
        """
        await self.connect()

        try:
            # Use aiodocker's prune API
            result = await self.docker.containers.prune()

            containers_deleted = len(result.get("ContainersDeleted", []))
            space_reclaimed = result.get("SpaceReclaimed", 0)

            return {
                "containers_deleted": containers_deleted,
                "space_reclaimed": space_reclaimed,
                "space_reclaimed_formatted": self._format_bytes(space_reclaimed),
            }

        except DockerError as e:
            raise RuntimeError(f"Failed to prune containers: {str(e)}")

    async def prune_volumes(self) -> Dict[str, Any]:
        """
        Remove unused volumes.

        Returns:
            Dictionary with pruning results:
            {
                "volumes_deleted": int,
                "space_reclaimed": int,
                "space_reclaimed_formatted": str
            }

        Raises:
            RuntimeError: If pruning fails
        """
        await self.connect()

        try:
            # Use aiodocker's prune API
            result = await self.docker.volumes.prune()

            volumes_deleted = len(result.get("VolumesDeleted", []))
            space_reclaimed = result.get("SpaceReclaimed", 0)

            return {
                "volumes_deleted": volumes_deleted,
                "space_reclaimed": space_reclaimed,
                "space_reclaimed_formatted": self._format_bytes(space_reclaimed),
            }

        except DockerError as e:
            raise RuntimeError(f"Failed to prune volumes: {str(e)}")

    async def prune_networks(self) -> Dict[str, Any]:
        """
        Remove unused networks.

        Returns:
            Dictionary with pruning results:
            {
                "networks_deleted": int
            }

        Raises:
            RuntimeError: If pruning fails
        """
        await self.connect()

        try:
            # Use aiodocker's prune API
            result = await self.docker.networks.prune()

            networks_deleted = len(result.get("NetworksDeleted", []))

            return {
                "networks_deleted": networks_deleted,
            }

        except DockerError as e:
            raise RuntimeError(f"Failed to prune networks: {str(e)}")

    async def prune_all(self) -> Dict[str, Any]:
        """
        Perform complete cleanup of all unused Docker resources.

        This will remove:
        - Unused images
        - Stopped containers
        - Unused volumes
        - Unused networks
        - Build cache

        Returns:
            Dictionary with combined pruning results:
            {
                "images": {...},
                "containers": {...},
                "volumes": {...},
                "networks": {...},
                "total_space_reclaimed": int,
                "total_space_reclaimed_formatted": str
            }

        Raises:
            RuntimeError: If pruning fails
        """
        # Run all prune operations
        images_result = await self.prune_images(all=True)
        containers_result = await self.prune_containers()
        volumes_result = await self.prune_volumes()
        networks_result = await self.prune_networks()

        # Calculate total space reclaimed
        total_space = (
            images_result["space_reclaimed"]
            + containers_result["space_reclaimed"]
            + volumes_result["space_reclaimed"]
        )

        return {
            "images": images_result,
            "containers": containers_result,
            "volumes": volumes_result,
            "networks": networks_result,
            "total_space_reclaimed": total_space,
            "total_space_reclaimed_formatted": self._format_bytes(total_space),
        }


# Global instance
docker_cleanup_service = DockerCleanupService()
