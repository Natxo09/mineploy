"""
Tests for health check endpoint.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test that health check endpoint returns OK."""
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_root_redirect(client: AsyncClient):
    """Test that root redirects to docs."""
    response = await client.get("/", follow_redirects=False)

    assert response.status_code in [200, 307, 308]  # OK or redirect
