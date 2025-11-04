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

    # Restricted paths (cannot be deleted or renamed)
    RESTRICTED_PATHS = {
        '/eula.txt',
        '/server.jar',
        '/.rcon-cli.env',
        '/.rcon-cli.yaml',
    }

    # Read-only paths (cannot be edited, but can be viewed)
    READ_ONLY_PATHS = {
        '/.rcon-cli.env',
        '/.rcon-cli.yaml',
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
        """Check if path is restricted (cannot be deleted or renamed)."""
        return path in self.RESTRICTED_PATHS

    def _is_read_only_path(self, path: str) -> bool:
        """Check if path is read-only (cannot be edited)."""
        return path in self.READ_ONLY_PATHS

    def _get_extension(self, filename: str) -> Optional[str]:
        """Get file extension without dot."""
        if '.' in filename:
            return filename.rsplit('.', 1)[1].lower()
        return None

    def _is_editable(self, filepath: str) -> bool:
        """Check if file can be edited in browser."""
        # Read-only files cannot be edited
        if self._is_read_only_path(filepath):
            return False

        # Check extension
        filename = os.path.basename(filepath)
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
            print(f"[DEBUG] list_files called with container_id={container_id}, path={path}")

            # Sanitize path
            path = self._sanitize_path(path)
            print(f"[DEBUG] Sanitized path: {path}")

            # Build full container path
            container_path = f"/data{path}"
            print(f"[DEBUG] Container path: {container_path}")

            container = self.docker.containers.container(container_id)
            print(f"[DEBUG] Got container object")

            # Get directory as tar archive
            # This works even if container is stopped
            tar_stream = await container.get_archive(container_path)
            print(f"[DEBUG] Got tar stream, type: {type(tar_stream)}")

            # Check if it's already a TarFile object or raw bytes
            if isinstance(tar_stream, tarfile.TarFile):
                tar_file = tar_stream
                print(f"[DEBUG] Using TarFile object directly")
            else:
                # Read tar data if it's bytes or a stream
                if hasattr(tar_stream, 'read'):
                    tar_data = tar_stream.read()
                else:
                    tar_data = tar_stream

                print(f"[DEBUG] Tar data size: {len(tar_data)} bytes")

                # Open tar file
                tar_file = tarfile.open(fileobj=io.BytesIO(tar_data))
                print(f"[DEBUG] Opened tar file from bytes")

            files = []
            tar_members = tar_file.getmembers()
            print(f"[DEBUG] Total tar members: {len(tar_members)}")

            # Docker returns tar with the last component of the path as root
            # For /data/ -> returns 'data/' as root
            # For /data/world -> returns 'world/' as root
            base_dir_name = os.path.basename(container_path.rstrip('/'))
            print(f"[DEBUG] Base dir name: '{base_dir_name}'")

            # Build expected prefix for tar members
            expected_prefix = base_dir_name + '/'
            print(f"[DEBUG] Expected prefix: '{expected_prefix}'")

            for idx, member in enumerate(tar_members):
                print(f"[DEBUG] Member {idx}: name={member.name}, type={member.type}, size={member.size}")

                # Skip the base directory itself
                if member.name == base_dir_name:
                    print(f"[DEBUG] Skipping base directory itself")
                    continue

                # Check if member is directly under the base directory
                if not member.name.startswith(expected_prefix):
                    print(f"[DEBUG] Skipping - doesn't start with expected prefix")
                    continue

                # Get relative name (remove base directory prefix)
                relative_name = member.name[len(expected_prefix):]
                print(f"[DEBUG] Relative name: '{relative_name}'")

                # Skip if empty (shouldn't happen but just in case)
                if not relative_name:
                    print(f"[DEBUG] Skipping - empty relative name")
                    continue

                # Skip if contains / (means it's in a subdirectory, not directly under current path)
                if '/' in relative_name:
                    print(f"[DEBUG] Skipping subdirectory item: {relative_name}")
                    continue

                name = relative_name

                # Determine type
                is_directory = member.isdir()
                file_type = FileType.DIRECTORY if is_directory else FileType.FILE

                # Get size (0 for directories)
                size = member.size if not is_directory else 0

                # Get modification time
                try:
                    modified = datetime.fromtimestamp(member.mtime) if member.mtime else None
                except (ValueError, OSError):
                    modified = None

                # Build relative path
                if path == '/':
                    file_path = f"/{name}"
                else:
                    file_path = f"{path}/{name}"

                print(f"[DEBUG] Adding file - name={name}, type={file_type}, size={size}")

                files.append(FileInfo(
                    name=name,
                    path=file_path,
                    type=file_type,
                    size=size,
                    modified=modified,
                    is_editable=self._is_editable(file_path) if not is_directory else False,
                    extension=self._get_extension(name) if not is_directory else None,
                ))

            tar_file.close()
            print(f"[DEBUG] Total files found: {len(files)}")

            # Sort: directories first, then files alphabetically
            files.sort(key=lambda f: (f.type == FileType.FILE, f.name.lower()))

            return files

        except DockerError as e:
            print(f"[ERROR] DockerError: status={e.status}, message={str(e)}")
            if e.status == 404:
                raise FileNotFoundError(f"Path not found: {path}")
            raise DockerError(e.status, {"message": f"Failed to list files: {str(e)}"})
        except Exception as e:
            print(f"[ERROR] Unexpected error: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

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

        # Check if path is read-only
        if self._is_read_only_path(path):
            raise ValueError(f"Cannot modify read-only file: {path}")

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
