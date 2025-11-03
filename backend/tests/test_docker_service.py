"""
Tests for Docker service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiodocker.exceptions import DockerError

from services.docker_service import DockerService
from models.server import ServerType, ServerStatus


@pytest.fixture
def docker_service():
    """Create a fresh DockerService instance."""
    return DockerService()


@pytest.fixture
def mock_docker():
    """Create a mock Docker client."""
    mock = MagicMock()
    mock.containers = MagicMock()
    return mock


@pytest.mark.asyncio
async def test_connect(docker_service):
    """Test connecting to Docker daemon."""
    with patch('services.docker_service.aiodocker.Docker') as mock_docker_class:
        await docker_service.connect()
        assert docker_service.docker is not None
        mock_docker_class.assert_called_once()


@pytest.mark.asyncio
async def test_close(docker_service):
    """Test closing Docker connection."""
    with patch('services.docker_service.aiodocker.Docker') as mock_docker_class:
        mock_instance = AsyncMock()
        mock_docker_class.return_value = mock_instance

        await docker_service.connect()
        await docker_service.close()

        mock_instance.close.assert_called_once()
        assert docker_service.docker is None


@pytest.mark.asyncio
async def test_get_server_image_config(docker_service):
    """Test getting server image configuration."""
    assert docker_service._get_server_image_config(ServerType.VANILLA) == "VANILLA"
    assert docker_service._get_server_image_config(ServerType.PAPER) == "PAPER"
    assert docker_service._get_server_image_config(ServerType.SPIGOT) == "SPIGOT"
    assert docker_service._get_server_image_config(ServerType.FABRIC) == "FABRIC"
    assert docker_service._get_server_image_config(ServerType.FORGE) == "FORGE"
    assert docker_service._get_server_image_config(ServerType.NEOFORGE) == "NEOFORGE"
    assert docker_service._get_server_image_config(ServerType.PURPUR) == "PURPUR"


@pytest.mark.asyncio
async def test_create_container_success(docker_service):
    """Test creating a container successfully."""
    with patch('services.docker_service.aiodocker.Docker') as mock_docker_class:
        mock_docker = AsyncMock()
        mock_container = AsyncMock()
        mock_docker_class.return_value = mock_docker
        mock_docker.containers.create = AsyncMock(return_value=mock_container)
        mock_container.show = AsyncMock(return_value={"Id": "test_container_id"})

        docker_service.docker = mock_docker

        container_id, info = await docker_service.create_container(
            container_name="test_container",
            server_type=ServerType.VANILLA,
            version="1.20.1",
            port=25565,
            rcon_port=25575,
            rcon_password="testpass",
            memory_mb=2048
        )

        assert container_id == "test_container_id"
        assert info["Id"] == "test_container_id"
        mock_docker.containers.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_container_failure(docker_service):
    """Test container creation failure."""
    with patch('services.docker_service.aiodocker.Docker') as mock_docker_class:
        mock_docker = AsyncMock()
        mock_docker_class.return_value = mock_docker
        mock_docker.containers.create = AsyncMock(side_effect=DockerError("Create failed", {"message": "error"}))

        docker_service.docker = mock_docker

        with pytest.raises(DockerError):
            await docker_service.create_container(
                container_name="test_container",
                server_type=ServerType.VANILLA,
                version="1.20.1",
                port=25565,
                rcon_port=25575,
                rcon_password="testpass",
                memory_mb=2048
            )


@pytest.mark.asyncio
async def test_start_container_success(docker_service):
    """Test starting a container."""
    with patch('services.docker_service.aiodocker.Docker') as mock_docker_class:
        mock_docker = AsyncMock()
        mock_container = AsyncMock()
        mock_docker_class.return_value = mock_docker
        mock_docker.containers.container = MagicMock(return_value=mock_container)
        mock_container.start = AsyncMock()

        docker_service.docker = mock_docker

        result = await docker_service.start_container("test_container_id")

        assert result is True
        mock_container.start.assert_called_once()


@pytest.mark.asyncio
async def test_start_container_failure(docker_service):
    """Test starting a container failure."""
    with patch('services.docker_service.aiodocker.Docker') as mock_docker_class:
        mock_docker = AsyncMock()
        mock_container = AsyncMock()
        mock_docker_class.return_value = mock_docker
        mock_docker.containers.container = MagicMock(return_value=mock_container)
        mock_container.start = AsyncMock(side_effect=DockerError("Start failed", {"message": "error"}))

        docker_service.docker = mock_docker

        with pytest.raises(DockerError):
            await docker_service.start_container("test_container_id")


@pytest.mark.asyncio
async def test_stop_container_success(docker_service):
    """Test stopping a container."""
    with patch('services.docker_service.aiodocker.Docker') as mock_docker_class:
        mock_docker = AsyncMock()
        mock_container = AsyncMock()
        mock_docker_class.return_value = mock_docker
        mock_docker.containers.container = MagicMock(return_value=mock_container)
        mock_container.stop = AsyncMock()

        docker_service.docker = mock_docker

        result = await docker_service.stop_container("test_container_id")

        assert result is True
        mock_container.stop.assert_called_once_with(timeout=30)


@pytest.mark.asyncio
async def test_restart_container_success(docker_service):
    """Test restarting a container."""
    with patch('services.docker_service.aiodocker.Docker') as mock_docker_class:
        mock_docker = AsyncMock()
        mock_container = AsyncMock()
        mock_docker_class.return_value = mock_docker
        mock_docker.containers.container = MagicMock(return_value=mock_container)
        mock_container.restart = AsyncMock()

        docker_service.docker = mock_docker

        result = await docker_service.restart_container("test_container_id")

        assert result is True
        mock_container.restart.assert_called_once_with(timeout=30)


@pytest.mark.asyncio
async def test_delete_container_success(docker_service):
    """Test deleting a container."""
    with patch('services.docker_service.aiodocker.Docker') as mock_docker_class:
        mock_docker = AsyncMock()
        mock_container = AsyncMock()
        mock_docker_class.return_value = mock_docker
        mock_docker.containers.container = MagicMock(return_value=mock_container)
        mock_container.delete = AsyncMock()

        docker_service.docker = mock_docker

        result = await docker_service.delete_container("test_container_id", force=True)

        assert result is True
        mock_container.delete.assert_called_once_with(force=True)


@pytest.mark.asyncio
async def test_get_container_status_running(docker_service):
    """Test getting container status - running."""
    with patch('services.docker_service.aiodocker.Docker') as mock_docker_class:
        mock_docker = AsyncMock()
        mock_container = AsyncMock()
        mock_docker_class.return_value = mock_docker
        mock_docker.containers.container = MagicMock(return_value=mock_container)
        mock_container.show = AsyncMock(return_value={"State": {"Status": "running"}})

        docker_service.docker = mock_docker

        status = await docker_service.get_container_status("test_container_id")

        assert status == ServerStatus.RUNNING


@pytest.mark.asyncio
async def test_get_container_status_stopped(docker_service):
    """Test getting container status - stopped."""
    with patch('services.docker_service.aiodocker.Docker') as mock_docker_class:
        mock_docker = AsyncMock()
        mock_container = AsyncMock()
        mock_docker_class.return_value = mock_docker
        mock_docker.containers.container = MagicMock(return_value=mock_container)
        mock_container.show = AsyncMock(return_value={"State": {"Status": "exited"}})

        docker_service.docker = mock_docker

        status = await docker_service.get_container_status("test_container_id")

        assert status == ServerStatus.STOPPED


@pytest.mark.asyncio
async def test_get_container_status_error(docker_service):
    """Test getting container status - error."""
    with patch('services.docker_service.aiodocker.Docker') as mock_docker_class:
        mock_docker = AsyncMock()
        mock_container = AsyncMock()
        mock_docker_class.return_value = mock_docker
        mock_docker.containers.container = MagicMock(return_value=mock_container)
        mock_container.show = AsyncMock(side_effect=DockerError("Not found", {"message": "error"}))

        docker_service.docker = mock_docker

        status = await docker_service.get_container_status("test_container_id")

        assert status == ServerStatus.ERROR


@pytest.mark.asyncio
async def test_get_container_stats_success(docker_service):
    """Test getting container statistics."""
    with patch('services.docker_service.aiodocker.Docker') as mock_docker_class:
        mock_docker = AsyncMock()
        mock_container = AsyncMock()
        mock_docker_class.return_value = mock_docker
        mock_docker.containers.container = MagicMock(return_value=mock_container)
        mock_container.stats = AsyncMock(return_value={
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000000000},
                "system_cpu_usage": 10000000000,
                "online_cpus": 4
            },
            "memory_stats": {
                "usage": 1073741824,  # 1GB
                "limit": 2147483648   # 2GB
            }
        })

        docker_service.docker = mock_docker

        stats = await docker_service.get_container_stats("test_container_id")

        assert stats is not None
        assert "cpu_percent" in stats
        assert "memory_usage_mb" in stats
        assert "memory_limit_mb" in stats
        assert stats["memory_usage_mb"] == 1024.0
        assert stats["memory_limit_mb"] == 2048.0


@pytest.mark.asyncio
async def test_get_container_stats_failure(docker_service):
    """Test getting container statistics failure."""
    with patch('services.docker_service.aiodocker.Docker') as mock_docker_class:
        mock_docker = AsyncMock()
        mock_container = AsyncMock()
        mock_docker_class.return_value = mock_docker
        mock_docker.containers.container = MagicMock(return_value=mock_container)
        mock_container.stats = AsyncMock(side_effect=DockerError("Stats failed", {"message": "error"}))

        docker_service.docker = mock_docker

        stats = await docker_service.get_container_stats("test_container_id")

        assert stats is None


@pytest.mark.asyncio
async def test_container_exists_true(docker_service):
    """Test checking if container exists - true."""
    with patch('services.docker_service.aiodocker.Docker') as mock_docker_class:
        mock_docker = AsyncMock()
        mock_docker_class.return_value = mock_docker
        mock_docker.containers.list = AsyncMock(return_value=[
            {"Names": ["/test_container"]}
        ])

        docker_service.docker = mock_docker

        exists = await docker_service.container_exists("test_container")

        assert exists is True


@pytest.mark.asyncio
async def test_container_exists_false(docker_service):
    """Test checking if container exists - false."""
    with patch('services.docker_service.aiodocker.Docker') as mock_docker_class:
        mock_docker = AsyncMock()
        mock_docker_class.return_value = mock_docker
        mock_docker.containers.list = AsyncMock(return_value=[
            {"Names": ["/other_container"]}
        ])

        docker_service.docker = mock_docker

        exists = await docker_service.container_exists("test_container")

        assert exists is False


@pytest.mark.asyncio
async def test_container_exists_docker_error(docker_service):
    """Test checking if container exists - Docker error."""
    with patch('services.docker_service.aiodocker.Docker') as mock_docker_class:
        mock_docker = AsyncMock()
        mock_docker_class.return_value = mock_docker
        mock_docker.containers.list = AsyncMock(side_effect=DockerError("List failed", {"message": "error"}))

        docker_service.docker = mock_docker

        exists = await docker_service.container_exists("test_container")

        assert exists is False
