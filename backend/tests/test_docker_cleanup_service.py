"""
Tests for Docker cleanup service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.docker_cleanup_service import DockerCleanupService


@pytest.fixture
def cleanup_service():
    """Create a DockerCleanupService instance."""
    return DockerCleanupService()


@pytest.fixture
def mock_docker():
    """Mock Docker client."""
    mock = MagicMock()
    mock.system = MagicMock()
    mock.images = MagicMock()
    mock.containers = MagicMock()
    mock.volumes = MagicMock()
    mock.networks = MagicMock()
    return mock


class TestFormatBytes:
    """Tests for _format_bytes method."""

    def test_format_zero_bytes(self, cleanup_service):
        assert cleanup_service._format_bytes(0) == "0 B"

    def test_format_bytes_exact(self, cleanup_service):
        assert cleanup_service._format_bytes(1024) == "1.0 KB"

    def test_format_kilobytes(self, cleanup_service):
        assert cleanup_service._format_bytes(2048) == "2.0 KB"

    def test_format_megabytes(self, cleanup_service):
        assert cleanup_service._format_bytes(1024 * 1024) == "1.0 MB"

    def test_format_gigabytes(self, cleanup_service):
        assert cleanup_service._format_bytes(2 * 1024 * 1024 * 1024) == "2.0 GB"

    def test_format_decimal_values(self, cleanup_service):
        result = cleanup_service._format_bytes(1536)  # 1.5 KB
        assert result == "1.5 KB"


class TestParseSizeString:
    """Tests for _parse_size_string method."""

    def test_parse_zero(self, cleanup_service):
        assert cleanup_service._parse_size_string("0B") == 0
        assert cleanup_service._parse_size_string("0") == 0

    def test_parse_bytes(self, cleanup_service):
        assert cleanup_service._parse_size_string("100B") == 100

    def test_parse_kilobytes(self, cleanup_service):
        assert cleanup_service._parse_size_string("1KB") == 1024
        assert cleanup_service._parse_size_string("2.5KB") == int(2.5 * 1024)

    def test_parse_megabytes(self, cleanup_service):
        assert cleanup_service._parse_size_string("1MB") == 1024 * 1024
        assert cleanup_service._parse_size_string("2.4MB") == int(2.4 * 1024 * 1024)

    def test_parse_gigabytes(self, cleanup_service):
        assert cleanup_service._parse_size_string("1GB") == 1024 * 1024 * 1024
        assert cleanup_service._parse_size_string("3.5GB") == int(3.5 * 1024 * 1024 * 1024)

    def test_parse_case_insensitive(self, cleanup_service):
        assert cleanup_service._parse_size_string("1gb") == 1024 * 1024 * 1024
        assert cleanup_service._parse_size_string("1Gb") == 1024 * 1024 * 1024

    def test_parse_with_spaces(self, cleanup_service):
        assert cleanup_service._parse_size_string(" 1 GB ") == 1024 * 1024 * 1024

    def test_parse_invalid_string(self, cleanup_service):
        assert cleanup_service._parse_size_string("invalid") == 0


@pytest.mark.asyncio
class TestGetDiskUsage:
    """Tests for get_disk_usage method."""

    async def test_get_disk_usage_success(self, cleanup_service, mock_docker):
        """Test successful disk usage retrieval."""
        # Mock images.list response
        mock_docker.images.list = AsyncMock(return_value=[
            {"Size": 1024 * 1024 * 1024},  # 1 GB
            {"Size": 512 * 1024 * 1024},    # 512 MB
        ])

        # Mock containers.list response
        mock_docker.containers.list = AsyncMock(return_value=[
            {"SizeRw": 100 * 1024 * 1024, "SizeRootFs": 50 * 1024 * 1024},  # 150 MB
        ])

        # Mock volumes.list response
        mock_docker.volumes.list = AsyncMock(return_value={
            "Volumes": [
                {"UsageData": {"Size": 2 * 1024 * 1024 * 1024}},  # 2 GB
                {"UsageData": {"Size": 500 * 1024 * 1024}},       # 500 MB
            ],
        })

        cleanup_service.docker = mock_docker

        result = await cleanup_service.get_disk_usage()

        # Verify structure
        assert "images" in result
        assert "containers" in result
        assert "volumes" in result
        assert "build_cache" in result
        assert "total" in result

        # Verify images
        assert result["images"]["count"] == 2
        assert result["images"]["size"] == 1024 * 1024 * 1024 + 512 * 1024 * 1024
        assert "size_formatted" in result["images"]

        # Verify containers
        assert result["containers"]["count"] == 1
        assert result["containers"]["size"] == 150 * 1024 * 1024

        # Verify volumes
        assert result["volumes"]["count"] == 2
        assert result["volumes"]["size"] == 2 * 1024 * 1024 * 1024 + 500 * 1024 * 1024

        # Verify build cache (should be 0 since not easily accessible)
        assert result["build_cache"]["size"] == 0

        # Verify total
        expected_total = (
            1024 * 1024 * 1024 + 512 * 1024 * 1024 +  # Images
            150 * 1024 * 1024 +                       # Containers
            2 * 1024 * 1024 * 1024 + 500 * 1024 * 1024  # Volumes
        )
        assert result["total"]["size"] == expected_total

    async def test_get_disk_usage_empty(self, cleanup_service, mock_docker):
        """Test disk usage with no resources."""
        mock_docker.images.list = AsyncMock(return_value=[])
        mock_docker.containers.list = AsyncMock(return_value=[])
        mock_docker.volumes.list = AsyncMock(return_value={"Volumes": []})

        cleanup_service.docker = mock_docker

        result = await cleanup_service.get_disk_usage()

        assert result["images"]["count"] == 0
        assert result["images"]["size"] == 0
        assert result["containers"]["count"] == 0
        assert result["volumes"]["count"] == 0
        assert result["total"]["size"] == 0

    async def test_get_disk_usage_volumes_without_usage_data(self, cleanup_service, mock_docker):
        """Test handling volumes without UsageData."""
        mock_docker.images.list = AsyncMock(return_value=[])
        mock_docker.containers.list = AsyncMock(return_value=[])
        mock_docker.volumes.list = AsyncMock(return_value={
            "Volumes": [
                {"UsageData": {"Size": 1024}},
                {},  # Volume without UsageData
            ],
        })

        cleanup_service.docker = mock_docker

        result = await cleanup_service.get_disk_usage()

        # Should only count volume with UsageData
        assert result["volumes"]["size"] == 1024


@pytest.mark.asyncio
class TestPruneImages:
    """Tests for prune_images method."""

    async def test_prune_images_success(self, cleanup_service, mock_docker):
        """Test successful image pruning."""
        mock_docker.images.prune = AsyncMock(return_value={
            "ImagesDeleted": [
                {"Deleted": "sha256:abc123"},
                {"Deleted": "sha256:def456"},
            ],
            "SpaceReclaimed": 2 * 1024 * 1024 * 1024,  # 2 GB
        })

        cleanup_service.docker = mock_docker

        result = await cleanup_service.prune_images()

        assert result["images_deleted"] == 2
        assert result["space_reclaimed"] == 2 * 1024 * 1024 * 1024
        assert result["space_reclaimed_formatted"] == "2.0 GB"

    async def test_prune_images_none_deleted(self, cleanup_service, mock_docker):
        """Test pruning when no images are deleted."""
        mock_docker.images.prune = AsyncMock(return_value={
            "ImagesDeleted": [],
            "SpaceReclaimed": 0,
        })

        cleanup_service.docker = mock_docker

        result = await cleanup_service.prune_images()

        assert result["images_deleted"] == 0
        assert result["space_reclaimed"] == 0


@pytest.mark.asyncio
class TestPruneContainers:
    """Tests for prune_containers method."""

    async def test_prune_containers_success(self, cleanup_service, mock_docker):
        """Test successful container pruning."""
        mock_docker.containers.prune = AsyncMock(return_value={
            "ContainersDeleted": ["container1", "container2", "container3"],
            "SpaceReclaimed": 500 * 1024 * 1024,  # 500 MB
        })

        cleanup_service.docker = mock_docker

        result = await cleanup_service.prune_containers()

        assert result["containers_deleted"] == 3
        assert result["space_reclaimed"] == 500 * 1024 * 1024
        assert "space_reclaimed_formatted" in result


@pytest.mark.asyncio
class TestPruneVolumes:
    """Tests for prune_volumes method."""

    async def test_prune_volumes_success(self, cleanup_service, mock_docker):
        """Test successful volume pruning."""
        mock_docker.volumes.prune = AsyncMock(return_value={
            "VolumesDeleted": ["vol1", "vol2"],
            "SpaceReclaimed": 1024 * 1024 * 1024,  # 1 GB
        })

        cleanup_service.docker = mock_docker

        result = await cleanup_service.prune_volumes()

        assert result["volumes_deleted"] == 2
        assert result["space_reclaimed"] == 1024 * 1024 * 1024
        assert result["space_reclaimed_formatted"] == "1.0 GB"


@pytest.mark.asyncio
class TestPruneNetworks:
    """Tests for prune_networks method."""

    async def test_prune_networks_success(self, cleanup_service, mock_docker):
        """Test successful network pruning."""
        mock_docker.networks.prune = AsyncMock(return_value={
            "NetworksDeleted": ["net1", "net2"],
        })

        cleanup_service.docker = mock_docker

        result = await cleanup_service.prune_networks()

        assert result["networks_deleted"] == 2


@pytest.mark.asyncio
class TestPruneAll:
    """Tests for prune_all method."""

    async def test_prune_all_success(self, cleanup_service, mock_docker):
        """Test successful complete pruning."""
        # Mock all prune methods
        mock_docker.images.prune = AsyncMock(return_value={
            "ImagesDeleted": [{"Deleted": "img1"}],
            "SpaceReclaimed": 1024 * 1024 * 1024,  # 1 GB
        })
        mock_docker.containers.prune = AsyncMock(return_value={
            "ContainersDeleted": ["cont1"],
            "SpaceReclaimed": 512 * 1024 * 1024,  # 512 MB
        })
        mock_docker.volumes.prune = AsyncMock(return_value={
            "VolumesDeleted": ["vol1"],
            "SpaceReclaimed": 256 * 1024 * 1024,  # 256 MB
        })
        mock_docker.networks.prune = AsyncMock(return_value={
            "NetworksDeleted": ["net1"],
        })

        cleanup_service.docker = mock_docker

        result = await cleanup_service.prune_all()

        # Verify all operations ran
        assert "images" in result
        assert "containers" in result
        assert "volumes" in result
        assert "networks" in result

        # Verify total space reclaimed
        expected_total = 1024 * 1024 * 1024 + 512 * 1024 * 1024 + 256 * 1024 * 1024
        assert result["total_space_reclaimed"] == expected_total
        assert "total_space_reclaimed_formatted" in result

        # Verify individual results
        assert result["images"]["images_deleted"] == 1
        assert result["containers"]["containers_deleted"] == 1
        assert result["volumes"]["volumes_deleted"] == 1
        assert result["networks"]["networks_deleted"] == 1
