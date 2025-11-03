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
            # Get ONLY Minecraft server images (itzg/minecraft-server)
            all_images = await self.docker.images.list()
            minecraft_images = [
                img for img in all_images
                if any("itzg/minecraft-server" in tag for tag in img.get("RepoTags", []))
            ]
            images_size = sum(img.get("Size", 0) for img in minecraft_images)
            images_count = len(minecraft_images)

            # Get ONLY Mineploy-managed containers (with label mineploy.managed=true)
            all_containers = await self.docker.containers.list(all=True)
            containers_size = 0
            mineploy_containers = []

            for container_obj in all_containers:
                try:
                    container_info = await container_obj.show()
                    labels = container_info.get("Config", {}).get("Labels", {})

                    # Only count Mineploy-managed containers
                    if labels.get("mineploy.managed") == "true":
                        mineploy_containers.append(container_obj)
                        size_rw = container_info.get("SizeRw", 0)
                        size_root = container_info.get("SizeRootFs", 0)
                        containers_size += size_rw + size_root
                except Exception:
                    # If we can't get info for this container, skip it
                    pass

            containers_count = len(mineploy_containers)

            # Get volumes - only count ORPHANED volumes (not in use)
            volumes_data = await self.docker.volumes.list()
            all_volumes = volumes_data.get("Volumes", []) if volumes_data else []

            # Get volumes in use by containers
            volumes_in_use = set()
            for container_obj in mineploy_containers:
                try:
                    container_info = await container_obj.show()
                    mounts = container_info.get("Mounts", [])
                    for mount in mounts:
                        if mount.get("Type") == "volume":
                            volumes_in_use.add(mount.get("Name"))
                except Exception:
                    pass

            # Only count orphaned volumes (not in use by any container)
            volumes_size = 0
            orphaned_volumes = []
            for v in all_volumes:
                volume_name = v.get("Name")
                if volume_name and volume_name not in volumes_in_use:
                    orphaned_volumes.append(v)
                    if isinstance(v, dict) and "UsageData" in v:
                        volumes_size += v.get("UsageData", {}).get("Size", 0)

            volumes_count = len(orphaned_volumes)

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
        Remove unused Minecraft server images (itzg/minecraft-server).

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
            # Get all images
            all_images = await self.docker.images.list()
            print(f"🔍 Total images found: {len(all_images)}")

            # Find Minecraft images that are not being used
            images_deleted = 0
            space_reclaimed = 0

            # Get list of images in use by containers
            containers = await self.docker.containers.list(all=True)
            images_in_use = set()

            for container_obj in containers:
                try:
                    container_info = await container_obj.show()
                    image_id = container_info.get("Image")
                    if image_id:
                        images_in_use.add(image_id)
                        print(f"📦 Container using image: {image_id[:12]}")
                except Exception:
                    pass

            print(f"🎯 Images in use: {len(images_in_use)}")

            # Delete unused Minecraft images
            minecraft_images = 0
            for img in all_images:
                repo_tags = img.get("RepoTags", [])
                image_id = img.get("Id")

                # Only delete itzg/minecraft-server images not in use
                if any("itzg/minecraft-server" in tag for tag in repo_tags):
                    minecraft_images += 1
                    print(f"🎮 Minecraft image found: {repo_tags} - ID: {image_id[:12]}")

                    if image_id not in images_in_use:
                        print(f"🗑️  Attempting to delete unused image: {image_id[:12]}")
                        try:
                            await self.docker.images.delete(image_id)
                            images_deleted += 1
                            space_reclaimed += img.get("Size", 0)
                            print(f"✅ Deleted image: {image_id[:12]}")
                        except Exception as e:
                            print(f"❌ Failed to delete image {image_id[:12]}: {e}")
                    else:
                        print(f"⏭️  Skipping in-use image: {image_id[:12]}")

            print(f"📊 Summary: {minecraft_images} Minecraft images, {images_deleted} deleted")

            return {
                "images_deleted": images_deleted,
                "space_reclaimed": space_reclaimed,
                "space_reclaimed_formatted": self._format_bytes(space_reclaimed),
            }

        except DockerError as e:
            raise RuntimeError(f"Failed to prune images: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to prune images: {str(e)}")

    async def prune_containers(self) -> Dict[str, Any]:
        """
        Remove stopped Mineploy-managed containers.

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
            # Get all containers
            all_containers = await self.docker.containers.list(all=True)

            containers_deleted = 0
            space_reclaimed = 0

            for container_obj in all_containers:
                try:
                    container_info = await container_obj.show()
                    labels = container_info.get("Config", {}).get("Labels", {})
                    state = container_info.get("State", {})

                    # Only delete Mineploy-managed stopped containers
                    if labels.get("mineploy.managed") == "true" and not state.get("Running", False):
                        size_rw = container_info.get("SizeRw", 0)
                        size_root = container_info.get("SizeRootFs", 0)

                        await container_obj.delete()
                        containers_deleted += 1
                        space_reclaimed += size_rw + size_root
                except Exception:
                    # Container might be running or have issues
                    pass

            return {
                "containers_deleted": containers_deleted,
                "space_reclaimed": space_reclaimed,
                "space_reclaimed_formatted": self._format_bytes(space_reclaimed),
            }

        except DockerError as e:
            raise RuntimeError(f"Failed to prune containers: {str(e)}")
        except Exception as e:
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
            # Get all volumes
            volumes_data = await self.docker.volumes.list()
            all_volumes = volumes_data.get("Volumes", []) if volumes_data else []

            # Get all containers to check which volumes are in use
            containers = await self.docker.containers.list(all=True)
            volumes_in_use = set()

            for container_obj in containers:
                try:
                    container_info = await container_obj.show()
                    mounts = container_info.get("Mounts", [])
                    for mount in mounts:
                        if mount.get("Type") == "volume":
                            volumes_in_use.add(mount.get("Name"))
                except Exception:
                    pass

            # Delete unused volumes
            volumes_deleted = 0
            space_reclaimed = 0

            for volume in all_volumes:
                volume_name = volume.get("Name")
                if volume_name and volume_name not in volumes_in_use:
                    try:
                        # Get size before deleting
                        if "UsageData" in volume:
                            space_reclaimed += volume.get("UsageData", {}).get("Size", 0)

                        # Delete volume
                        await self.docker.volumes.delete(volume_name)
                        volumes_deleted += 1
                    except Exception:
                        # Volume might be in use or protected
                        pass

            return {
                "volumes_deleted": volumes_deleted,
                "space_reclaimed": space_reclaimed,
                "space_reclaimed_formatted": self._format_bytes(space_reclaimed),
            }

        except DockerError as e:
            raise RuntimeError(f"Failed to prune volumes: {str(e)}")
        except Exception as e:
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
            # Get all networks
            networks = await self.docker.networks.list()

            # Get networks in use by containers
            containers = await self.docker.containers.list(all=True)
            networks_in_use = set()

            for container_obj in containers:
                try:
                    container_info = await container_obj.show()
                    network_settings = container_info.get("NetworkSettings", {})
                    networks_dict = network_settings.get("Networks", {})
                    for network_name in networks_dict.keys():
                        networks_in_use.add(network_name)
                except Exception:
                    pass

            # Delete unused networks (except default ones)
            networks_deleted = 0
            protected_networks = {"bridge", "host", "none", "minecraft_network", "mineploy_network"}

            for network in networks:
                network_name = network.get("Name")
                network_id = network.get("Id")

                # Don't delete protected networks or networks in use
                if network_name and network_name not in protected_networks and network_name not in networks_in_use:
                    try:
                        await self.docker.networks.delete(network_id or network_name)
                        networks_deleted += 1
                    except Exception:
                        # Network might be in use or protected
                        pass

            return {
                "networks_deleted": networks_deleted,
            }

        except DockerError as e:
            raise RuntimeError(f"Failed to prune networks: {str(e)}")
        except Exception as e:
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
