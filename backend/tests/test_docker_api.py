"""
Tests for Docker cleanup API endpoints.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from models.user import UserRole


@pytest.mark.asyncio
class TestDockerDiskUsageEndpoint:
    """Tests for GET /api/v1/docker/disk-usage endpoint."""

    async def test_get_disk_usage_as_admin(self, client: AsyncClient, admin_token: str):
        """Test admin can get disk usage."""
        mock_usage = {
            "images": {
                "size": 2400000000,
                "size_formatted": "2.4 GB",
                "count": 5
            },
            "containers": {
                "size": 156000000,
                "size_formatted": "156.0 MB",
                "count": 3
            },
            "volumes": {
                "size": 3800000000,
                "size_formatted": "3.8 GB",
                "count": 12
            },
            "build_cache": {
                "size": 0,
                "size_formatted": "0 B"
            },
            "total": {
                "size": 6356000000,
                "size_formatted": "6.4 GB"
            }
        }

        with patch('api.docker.docker_cleanup_service.get_disk_usage', new=AsyncMock(return_value=mock_usage)):
            response = await client.get(
                "/api/v1/docker/disk-usage",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        assert response.status_code == 200
        data = response.json()

        assert "images" in data
        assert "containers" in data
        assert "volumes" in data
        assert "build_cache" in data
        assert "total" in data

        assert data["images"]["count"] == 5
        assert data["total"]["size_formatted"] == "6.4 GB"

    async def test_get_disk_usage_as_moderator(self, client: AsyncClient, moderator_token: str):
        """Test moderator cannot get disk usage (403)."""
        response = await client.get(
            "/api/v1/docker/disk-usage",
            headers={"Authorization": f"Bearer {moderator_token}"}
        )

        assert response.status_code == 403

    async def test_get_disk_usage_as_viewer(self, client: AsyncClient, viewer_token: str):
        """Test viewer cannot get disk usage (403)."""
        response = await client.get(
            "/api/v1/docker/disk-usage",
            headers={"Authorization": f"Bearer {viewer_token}"}
        )

        assert response.status_code == 403

    async def test_get_disk_usage_unauthenticated(self, client: AsyncClient):
        """Test unauthenticated user cannot get disk usage (403)."""
        response = await client.get("/api/v1/docker/disk-usage")

        assert response.status_code == 403

    async def test_get_disk_usage_error(self, client: AsyncClient, admin_token: str):
        """Test error handling when disk usage retrieval fails."""
        with patch('api.docker.docker_cleanup_service.get_disk_usage',
                   new=AsyncMock(side_effect=RuntimeError("Docker error"))):
            response = await client.get(
                "/api/v1/docker/disk-usage",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        assert response.status_code == 500


@pytest.mark.asyncio
class TestPruneImagesEndpoint:
    """Tests for POST /api/v1/docker/prune-images endpoint."""

    async def test_prune_images_as_admin(self, client: AsyncClient, admin_token: str):
        """Test admin can prune images."""
        mock_result = {
            "images_deleted": 3,
            "space_reclaimed": 2000000000,
            "space_reclaimed_formatted": "2.0 GB"
        }

        with patch('api.docker.docker_cleanup_service.prune_images', new=AsyncMock(return_value=mock_result)):
            response = await client.post(
                "/api/v1/docker/prune-images",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        assert response.status_code == 200
        data = response.json()

        assert data["images_deleted"] == 3
        assert data["space_reclaimed"] == 2000000000
        assert data["space_reclaimed_formatted"] == "2.0 GB"

    async def test_prune_images_as_moderator(self, client: AsyncClient, moderator_token: str):
        """Test moderator cannot prune images (403)."""
        response = await client.post(
            "/api/v1/docker/prune-images",
            headers={"Authorization": f"Bearer {moderator_token}"}
        )

        assert response.status_code == 403

    async def test_prune_images_unauthenticated(self, client: AsyncClient):
        """Test unauthenticated user cannot prune images (403)."""
        response = await client.post("/api/v1/docker/prune-images")

        assert response.status_code == 403


@pytest.mark.asyncio
class TestPruneContainersEndpoint:
    """Tests for POST /api/v1/docker/prune-containers endpoint."""

    async def test_prune_containers_as_admin(self, client: AsyncClient, admin_token: str):
        """Test admin can prune containers."""
        mock_result = {
            "containers_deleted": 5,
            "space_reclaimed": 500000000,
            "space_reclaimed_formatted": "500.0 MB"
        }

        with patch('api.docker.docker_cleanup_service.prune_containers', new=AsyncMock(return_value=mock_result)):
            response = await client.post(
                "/api/v1/docker/prune-containers",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        assert response.status_code == 200
        data = response.json()

        assert data["containers_deleted"] == 5
        assert data["space_reclaimed_formatted"] == "500.0 MB"

    async def test_prune_containers_as_viewer(self, client: AsyncClient, viewer_token: str):
        """Test viewer cannot prune containers (403)."""
        response = await client.post(
            "/api/v1/docker/prune-containers",
            headers={"Authorization": f"Bearer {viewer_token}"}
        )

        assert response.status_code == 403


@pytest.mark.asyncio
class TestPruneVolumesEndpoint:
    """Tests for POST /api/v1/docker/prune-volumes endpoint."""

    async def test_prune_volumes_as_admin(self, client: AsyncClient, admin_token: str):
        """Test admin can prune volumes."""
        mock_result = {
            "volumes_deleted": 8,
            "space_reclaimed": 1500000000,
            "space_reclaimed_formatted": "1.5 GB"
        }

        with patch('api.docker.docker_cleanup_service.prune_volumes', new=AsyncMock(return_value=mock_result)):
            response = await client.post(
                "/api/v1/docker/prune-volumes",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        assert response.status_code == 200
        data = response.json()

        assert data["volumes_deleted"] == 8
        assert data["space_reclaimed"] == 1500000000

    async def test_prune_volumes_unauthorized(self, client: AsyncClient, moderator_token: str):
        """Test moderator cannot prune volumes (403)."""
        response = await client.post(
            "/api/v1/docker/prune-volumes",
            headers={"Authorization": f"Bearer {moderator_token}"}
        )

        assert response.status_code == 403


@pytest.mark.asyncio
class TestPruneNetworksEndpoint:
    """Tests for POST /api/v1/docker/prune-networks endpoint."""

    async def test_prune_networks_as_admin(self, client: AsyncClient, admin_token: str):
        """Test admin can prune networks."""
        mock_result = {
            "networks_deleted": 2
        }

        with patch('api.docker.docker_cleanup_service.prune_networks', new=AsyncMock(return_value=mock_result)):
            response = await client.post(
                "/api/v1/docker/prune-networks",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        assert response.status_code == 200
        data = response.json()

        assert data["networks_deleted"] == 2

    async def test_prune_networks_unauthorized(self, client: AsyncClient, viewer_token: str):
        """Test viewer cannot prune networks (403)."""
        response = await client.post(
            "/api/v1/docker/prune-networks",
            headers={"Authorization": f"Bearer {viewer_token}"}
        )

        assert response.status_code == 403


@pytest.mark.asyncio
class TestPruneAllEndpoint:
    """Tests for POST /api/v1/docker/prune-all endpoint."""

    async def test_prune_all_as_admin(self, client: AsyncClient, admin_token: str):
        """Test admin can perform complete cleanup."""
        mock_result = {
            "images": {
                "images_deleted": 3,
                "space_reclaimed": 2000000000,
                "space_reclaimed_formatted": "2.0 GB"
            },
            "containers": {
                "containers_deleted": 5,
                "space_reclaimed": 500000000,
                "space_reclaimed_formatted": "500.0 MB"
            },
            "volumes": {
                "volumes_deleted": 8,
                "space_reclaimed": 1500000000,
                "space_reclaimed_formatted": "1.5 GB"
            },
            "networks": {
                "networks_deleted": 2
            },
            "total_space_reclaimed": 4000000000,
            "total_space_reclaimed_formatted": "4.0 GB"
        }

        with patch('api.docker.docker_cleanup_service.prune_all', new=AsyncMock(return_value=mock_result)):
            response = await client.post(
                "/api/v1/docker/prune-all",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        assert response.status_code == 200
        data = response.json()

        assert "images" in data
        assert "containers" in data
        assert "volumes" in data
        assert "networks" in data
        assert "total_space_reclaimed" in data

        assert data["images"]["images_deleted"] == 3
        assert data["containers"]["containers_deleted"] == 5
        assert data["volumes"]["volumes_deleted"] == 8
        assert data["networks"]["networks_deleted"] == 2
        assert data["total_space_reclaimed_formatted"] == "4.0 GB"

    async def test_prune_all_as_moderator(self, client: AsyncClient, moderator_token: str):
        """Test moderator cannot perform complete cleanup (403)."""
        response = await client.post(
            "/api/v1/docker/prune-all",
            headers={"Authorization": f"Bearer {moderator_token}"}
        )

        assert response.status_code == 403

    async def test_prune_all_unauthenticated(self, client: AsyncClient):
        """Test unauthenticated user cannot perform cleanup (403)."""
        response = await client.post("/api/v1/docker/prune-all")

        assert response.status_code == 403

    async def test_prune_all_error(self, client: AsyncClient, admin_token: str):
        """Test error handling when cleanup fails."""
        with patch('api.docker.docker_cleanup_service.prune_all',
                   new=AsyncMock(side_effect=RuntimeError("Cleanup failed"))):
            response = await client.post(
                "/api/v1/docker/prune-all",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        assert response.status_code == 500
