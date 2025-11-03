"""
Tests for core configuration.
"""

import pytest
from core.config import settings


def test_settings_load():
    """Test that settings load correctly."""
    assert settings.app_name is not None
    assert settings.api_port > 0
    assert settings.jwt_algorithm == "HS256"


def test_database_url_mysql():
    """Test MySQL database URL generation."""
    assert "mysql" in settings.database_url
    assert "+aiomysql://" in settings.database_url
    assert settings.db_host in settings.database_url
    assert settings.db_name in settings.database_url


def test_cors_origins_parsing():
    """Test that CORS origins are properly parsed."""
    assert isinstance(settings.cors_origins, list)
    assert len(settings.cors_origins) > 0


def test_port_ranges():
    """Test that port ranges are valid."""
    assert settings.server_port_range_start < settings.server_port_range_end
    assert settings.rcon_port_range_start < settings.rcon_port_range_end
    assert settings.server_port_range_end > 25565
