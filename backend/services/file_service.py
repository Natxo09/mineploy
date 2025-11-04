"""
Service for managing files in Minecraft server containers.
"""

import aiodocker
from aiodocker.exceptions import DockerError
from typing import Optional, List
import tarfile
import io
import os
from datetime import datetime

from core.config import settings
from schemas.files import FileInfo, FileType


class FileService:
    """Service for managing files in Docker containers."""

    # Editable file extensions (can be edited in browser)
    EDITABLE_EXTENSIONS = {
        'txt', 'log', 'properties', 'json', 'yml', 'yaml',
        'toml', 'conf', 'cfg', 'ini', 'xml', 'md'
    }

    # Restricted paths (cannot be deleted or modified)
    RESTRICTED_PATHS = {
        '/eula.txt',
        '/server.jar',
    }

    # Max file size for upload (50MB)
    MAX_UPLOAD_SIZE = 50 * 1024 * 1024

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

    def _sanitize_path(self, path: str) -> str:
        """
        Sanitize and normalize path.

        Args:
            path: Path to sanitize

        Returns:
            Sanitized path starting with /

        Raises:
            ValueError: If path contains traversal attempts
        """
        # Remove leading/trailing whitespace
        path = path.strip()

        # Ensure starts with /
        if not path.startswith('/'):
            path = '/' + path

        # Check for path traversal
        if '..' in path:
            raise ValueError("Path traversal is not allowed")

        # Normalize path
        path = os.path.normpath(path)

        # Ensure still starts with / after normalization
        if not path.startswith('/'):
            path = '/' + path

        return path

    def _is_restricted_path(self, path: str) -> bool:
        """Check if path is restricted."""
        return path in self.RESTRICTED_PATHS

    def _get_extension(self, filename: str) -> Optional[str]:
        """Get file extension without dot."""
        if '.' in filename:
            return filename.rsplit('.', 1)[1].lower()
        return None

    def _is_editable(self, filename: str) -> bool:
        """Check if file can be edited in browser."""
        ext = self._get_extension(filename)
        return ext in self.EDITABLE_EXTENSIONS if ext else False

    async def list_files(self, container_id: str, path: str = "/") -> List[FileInfo]:
        """
        List files in a directory within the container.

        Args:
            container_id: Docker container ID
            path: Directory path to list (relative to /data)

        Returns:
            List of FileInfo objects

        Raises:
            DockerError: If listing fails
        """
        await self.connect()

        try:
            # Sanitize path
            path = self._sanitize_path(path)

            # Build full container path
            container_path = f"/data{path}"

            container = self.docker.containers.container(container_id)

            # Execute ls command to list directory
            # Using exec instead of get_archive for better directory listing
            exec_instance = await container.exec(
                cmd=['ls', '-la', '--time-style=+%Y-%m-%dT%H:%M:%S', container_path],
            )

            # Get output
            output = await exec_instance.start(detach=False)
            output_str = output.decode('utf-8') if isinstance(output, bytes) else output

            files = []
            lines = output_str.strip().split('\n')

            # Skip first line (total) and parse each line
            for line in lines[1:]:
                if not line.strip():
                    continue

                parts = line.split()
                if len(parts) < 9:
                    continue

                # Parse ls -la output
                permissions = parts[0]
                size_str = parts[4]
                date_str = parts[5]
                time_str = parts[6]
                name = ' '.join(parts[7:])

                # Skip . and ..
                if name in ['.', '..']:
                    continue

                # Determine type
                is_directory = permissions.startswith('d')
                file_type = FileType.DIRECTORY if is_directory else FileType.FILE

                # Parse size
                try:
                    size = int(size_str) if not is_directory else 0
                except ValueError:
                    size = 0

                # Parse timestamp
                try:
                    timestamp_str = f"{date_str}T{time_str}"
                    modified = datetime.fromisoformat(timestamp_str)
                except (ValueError, TypeError):
                    modified = None

                # Build relative path
                if path == '/':
                    file_path = f"/{name}"
                else:
                    file_path = f"{path}/{name}"

                files.append(FileInfo(
                    name=name,
                    path=file_path,
                    type=file_type,
                    size=size,
                    modified=modified,
                    is_editable=self._is_editable(name) if not is_directory else False,
                    extension=self._get_extension(name) if not is_directory else None,
                ))

            # Sort: directories first, then files alphabetically
            files.sort(key=lambda f: (f.type == FileType.FILE, f.name.lower()))

            return files

        except DockerError as e:
            if e.status == 404:
                raise FileNotFoundError(f"Path not found: {path}")
            raise DockerError(e.status, {"message": f"Failed to list files: {str(e)}"})

    async def read_file(self, container_id: str, path: str) -> bytes:
        """
        Read file content from container.

        Args:
            container_id: Docker container ID
            path: File path (relative to /data)

        Returns:
            File content as bytes

        Raises:
            DockerError: If read fails
            FileNotFoundError: If file doesn't exist
        """
        await self.connect()

        try:
            # Sanitize path
            path = self._sanitize_path(path)

            # Build full container path
            container_path = f"/data{path}"

            container = self.docker.containers.container(container_id)

            # Get file as tar archive
            tar_obj = await container.get_archive(container_path)

            # Handle tar object
            if isinstance(tar_obj, tarfile.TarFile):
                tar_file = tar_obj
            else:
                if hasattr(tar_obj, 'read'):
                    tar_data = tar_obj.read()
                else:
                    tar_data = tar_obj
                tar_file = tarfile.open(fileobj=io.BytesIO(tar_data))

            # Extract file from tar
            filename = os.path.basename(path)
            file_obj = tar_file.extractfile(filename)

            if file_obj is None:
                raise FileNotFoundError(f"File not found: {path}")

            content = file_obj.read()
            return content

        except DockerError as e:
            if e.status == 404:
                raise FileNotFoundError(f"File not found: {path}")
            raise DockerError(e.status, {"message": f"Failed to read file: {str(e)}"})

    async def write_file(self, container_id: str, path: str, content: bytes) -> bool:
        """
        Write file to container.

        Args:
            container_id: Docker container ID
            path: File path (relative to /data)
            content: File content as bytes

        Returns:
            True if write was successful

        Raises:
            DockerError: If write fails
            ValueError: If path is restricted or content too large
        """
        await self.connect()

        # Sanitize path
        path = self._sanitize_path(path)

        # Check if path is restricted
        if self._is_restricted_path(path):
            raise ValueError(f"Cannot modify restricted file: {path}")

        # Check file size
        if len(content) > self.MAX_UPLOAD_SIZE:
            raise ValueError(f"File size exceeds maximum allowed size of {self.MAX_UPLOAD_SIZE} bytes")

        try:
            container = self.docker.containers.container(container_id)

            # Create tar archive in memory
            tar_buffer = io.BytesIO()
            tar = tarfile.TarFile(fileobj=tar_buffer, mode='w')

            # Add file to tar
            filename = os.path.basename(path)
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(content)
            tarinfo.mode = 0o644
            # Set ownership to match container user (uid=1000, gid=1000)
            tarinfo.uid = 1000
            tarinfo.gid = 1000

            tar.addfile(tarinfo, io.BytesIO(content))
            tar.close()

            # Upload tar to container
            tar_buffer.seek(0)

            # Get parent directory
            parent_dir = os.path.dirname(path)
            if parent_dir == '':
                parent_dir = '/'
            container_parent = f"/data{parent_dir}"

            await container.put_archive(container_parent, tar_buffer.read())

            return True

        except DockerError as e:
            raise DockerError(e.status, {"message": f"Failed to write file: {str(e)}"})

    async def delete_file(self, container_id: str, path: str) -> bool:
        """
        Delete file or directory from container.

        Args:
            container_id: Docker container ID
            path: File or directory path (relative to /data)

        Returns:
            True if deletion was successful

        Raises:
            DockerError: If deletion fails
            ValueError: If path is restricted
        """
        await self.connect()

        # Sanitize path
        path = self._sanitize_path(path)

        # Check if path is restricted
        if self._is_restricted_path(path):
            raise ValueError(f"Cannot delete restricted file: {path}")

        try:
            container = self.docker.containers.container(container_id)

            # Build full container path
            container_path = f"/data{path}"

            # Execute rm command
            exec_instance = await container.exec(
                cmd=['rm', '-rf', container_path],
            )

            await exec_instance.start(detach=False)

            return True

        except DockerError as e:
            raise DockerError(e.status, {"message": f"Failed to delete file: {str(e)}"})

    async def create_folder(self, container_id: str, path: str, name: str) -> bool:
        """
        Create a new folder in container.

        Args:
            container_id: Docker container ID
            path: Parent directory path (relative to /data)
            name: Folder name

        Returns:
            True if creation was successful

        Raises:
            DockerError: If creation fails
        """
        await self.connect()

        # Sanitize path
        path = self._sanitize_path(path)

        # Validate name
        if '/' in name or '..' in name:
            raise ValueError("Invalid folder name")

        try:
            container = self.docker.containers.container(container_id)

            # Build full container path
            if path == '/':
                container_path = f"/data/{name}"
            else:
                container_path = f"/data{path}/{name}"

            # Execute mkdir command
            exec_instance = await container.exec(
                cmd=['mkdir', '-p', container_path],
            )

            await exec_instance.start(detach=False)

            # Set ownership
            chown_exec = await container.exec(
                cmd=['chown', '1000:1000', container_path],
            )
            await chown_exec.start(detach=False)

            return True

        except DockerError as e:
            raise DockerError(e.status, {"message": f"Failed to create folder: {str(e)}"})

    async def rename_file(self, container_id: str, old_path: str, new_name: str) -> bool:
        """
        Rename a file or directory in container.

        Args:
            container_id: Docker container ID
            old_path: Current path (relative to /data)
            new_name: New name (not full path)

        Returns:
            True if rename was successful

        Raises:
            DockerError: If rename fails
            ValueError: If path is restricted or name is invalid
        """
        await self.connect()

        # Sanitize path
        old_path = self._sanitize_path(old_path)

        # Check if path is restricted
        if self._is_restricted_path(old_path):
            raise ValueError(f"Cannot rename restricted file: {old_path}")

        # Validate new name
        if '/' in new_name or '..' in new_name:
            raise ValueError("Invalid new name")

        try:
            container = self.docker.containers.container(container_id)

            # Build full container paths
            old_container_path = f"/data{old_path}"

            parent_dir = os.path.dirname(old_path)
            if parent_dir == '':
                parent_dir = '/'

            if parent_dir == '/':
                new_container_path = f"/data/{new_name}"
            else:
                new_container_path = f"/data{parent_dir}/{new_name}"

            # Execute mv command
            exec_instance = await container.exec(
                cmd=['mv', old_container_path, new_container_path],
            )

            await exec_instance.start(detach=False)

            return True

        except DockerError as e:
            raise DockerError(e.status, {"message": f"Failed to rename file: {str(e)}"})


# Global instance
file_service = FileService()
