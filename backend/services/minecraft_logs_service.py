"""
Service for managing Minecraft server logs.

Handles reading, streaming, and filtering logs from Minecraft servers
running in Docker containers.
"""

import gzip
import re
from datetime import datetime
from typing import List, Dict, Optional, AsyncGenerator
from aiodocker.exceptions import DockerError

from services.docker_service import docker_service


class LogFile:
    """Represents a Minecraft log file."""

    def __init__(self, name: str, size: int, modified_time: datetime, is_compressed: bool):
        self.name = name
        self.size = size
        self.modified_time = modified_time
        self.is_compressed = is_compressed


class MinecraftLogsService:
    """Service for Minecraft log operations."""

    # Patterns to identify Minecraft log lines (vs Docker/system logs)
    MINECRAFT_LOG_PATTERNS = [
        r'\[Server thread/',           # [Server thread/INFO]
        r'\[Async Chat Thread',        # [Async Chat Thread/INFO]
        r'\[User Authenticator',       # [User Authenticator #1/INFO]
        r'\[Server console handler',   # [Server console handler/INFO]
        r'\[Worker-Main-\d+',          # [Worker-Main-1/INFO]
        r'\[Render thread/',           # [Render thread/INFO]
        r'\[main/',                    # [main/INFO]
    ]

    # Patterns to identify Docker/system log lines
    DOCKER_LOG_PATTERNS = [
        r'\[init\]',                   # [init] messages
        r'mc-image-helper',            # mc-image-helper output
        r'Unpacking',                  # Unpacking messages
        r'Downloading',                # Download progress
        r'Resolving',                  # Resolving dependencies
    ]

    def __init__(self):
        """Initialize the service."""
        self.logs_dir = "/data/logs"

    async def list_log_files(self, container_id: str) -> List[Dict[str, any]]:
        """
        List all log files in the Minecraft server's logs directory.

        Args:
            container_id: Docker container ID

        Returns:
            List of log file metadata dictionaries

        Raises:
            DockerError: If unable to access container
        """
        try:
            # List files in logs directory
            exit_code, output = await docker_service.exec_command(
                container_id,
                ['sh', '-c', f'ls -lA --time-style=+%s {self.logs_dir} 2>/dev/null || echo ""']
            )

            if exit_code != 0 or not output.strip():
                # Logs directory doesn't exist yet (server never started)
                return []

            files = []
            for line in output.strip().split('\n'):
                if not line or line.startswith('total'):
                    continue

                parts = line.split()
                if len(parts) < 9:
                    continue

                # Parse ls -l output: permissions links owner group size timestamp filename
                filename = parts[-1]
                size = int(parts[4])
                timestamp = int(parts[5])

                # Skip directories and special files
                if parts[0].startswith('d') or filename in ['.', '..']:
                    continue

                # Determine if compressed
                is_compressed = filename.endswith('.gz')

                files.append({
                    'name': filename,
                    'size': size,
                    'modified_time': datetime.fromtimestamp(timestamp).isoformat(),
                    'is_compressed': is_compressed,
                })

            # Sort by modified time (newest first)
            files.sort(key=lambda x: x['modified_time'], reverse=True)

            return files

        except DockerError as e:
            raise DockerError(e.status, {"message": f"Failed to list log files: {str(e)}"})

    async def read_log_file(
        self,
        container_id: str,
        filename: str,
        max_lines: Optional[int] = None
    ) -> str:
        """
        Read a specific log file from the Minecraft server.

        Args:
            container_id: Docker container ID
            filename: Name of the log file (e.g., "latest.log", "2024-01-15-1.log.gz")
            max_lines: Maximum number of lines to return (from end of file)

        Returns:
            Log file contents as string

        Raises:
            DockerError: If unable to read file
        """
        try:
            file_path = f"{self.logs_dir}/{filename}"

            # Check if file is compressed
            if filename.endswith('.gz'):
                # Decompress and read
                if max_lines:
                    command = ['sh', '-c', f'zcat {file_path} 2>/dev/null | tail -n {max_lines}']
                else:
                    command = ['sh', '-c', f'zcat {file_path} 2>/dev/null']
            else:
                # Read regular file
                if max_lines:
                    command = ['tail', '-n', str(max_lines), file_path]
                else:
                    command = ['cat', file_path]

            exit_code, output = await docker_service.exec_command(container_id, command)

            if exit_code != 0:
                raise DockerError(404, {"message": f"Log file not found: {filename}"})

            return output

        except DockerError as e:
            raise DockerError(e.status, {"message": f"Failed to read log file: {str(e)}"})

    async def stream_latest_log(
        self,
        container_id: str,
        lines: int = 50
    ) -> AsyncGenerator[str, None]:
        """
        Stream the latest.log file in real-time (like tail -f).

        Args:
            container_id: Docker container ID
            lines: Number of initial lines to show

        Yields:
            Log lines as they are written

        Note:
            This is a generator that yields lines as they appear.
            The caller is responsible for managing the async iteration.
        """
        # This will be implemented in Phase 3 when we integrate with WebSocket
        # For now, we'll provide the basic structure

        # Read initial lines
        file_path = f"{self.logs_dir}/latest.log"

        try:
            # Get initial lines
            exit_code, output = await docker_service.exec_command(
                container_id,
                ['tail', '-n', str(lines), file_path]
            )

            if exit_code == 0 and output:
                for line in output.split('\n'):
                    if line.strip():
                        yield line + '\n'

            # TODO: Implement continuous streaming with 'tail -f'
            # This requires maintaining a persistent exec session
            # Will be implemented in Phase 3 with WebSocket integration

        except DockerError:
            # File might not exist yet
            yield "[Waiting for server logs...]\n"

    def filter_minecraft_logs(self, logs: str) -> str:
        """
        Filter logs to only include Minecraft server logs (exclude Docker/system logs).

        Args:
            logs: Raw log content

        Returns:
            Filtered log content with only Minecraft logs
        """
        filtered_lines = []

        for line in logs.split('\n'):
            if not line.strip():
                filtered_lines.append(line)
                continue

            # Check if line matches Minecraft patterns
            is_minecraft = any(
                re.search(pattern, line)
                for pattern in self.MINECRAFT_LOG_PATTERNS
            )

            # Check if line matches Docker patterns
            is_docker = any(
                re.search(pattern, line)
                for pattern in self.DOCKER_LOG_PATTERNS
            )

            # Include line if it's identified as Minecraft or not identified as Docker
            if is_minecraft or not is_docker:
                filtered_lines.append(line)

        return '\n'.join(filtered_lines)

    def filter_docker_logs(self, logs: str) -> str:
        """
        Filter logs to only include Docker/system logs (exclude Minecraft logs).

        Args:
            logs: Raw log content

        Returns:
            Filtered log content with only Docker/system logs
        """
        filtered_lines = []

        for line in logs.split('\n'):
            if not line.strip():
                continue

            # Check if line matches Docker patterns
            is_docker = any(
                re.search(pattern, line)
                for pattern in self.DOCKER_LOG_PATTERNS
            )

            # Check if line matches Minecraft patterns
            is_minecraft = any(
                re.search(pattern, line)
                for pattern in self.MINECRAFT_LOG_PATTERNS
            )

            # Include line if it's identified as Docker or not identified as Minecraft
            if is_docker or not is_minecraft:
                filtered_lines.append(line)

        return '\n'.join(filtered_lines)

    async def get_latest_log_size(self, container_id: str) -> Optional[int]:
        """
        Get the size of the latest.log file.

        Args:
            container_id: Docker container ID

        Returns:
            File size in bytes, or None if file doesn't exist
        """
        try:
            file_path = f"{self.logs_dir}/latest.log"
            exit_code, output = await docker_service.exec_command(
                container_id,
                ['sh', '-c', f'stat -c %s {file_path} 2>/dev/null']
            )

            if exit_code == 0 and output.strip():
                return int(output.strip())

            return None

        except (DockerError, ValueError):
            return None


# Global instance
minecraft_logs_service = MinecraftLogsService()
