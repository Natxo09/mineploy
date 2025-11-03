"""
Tests for authentication endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, admin_user):
    """Test successful login with valid credentials."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"


@pytest.mark.asyncio
async def test_login_invalid_username(client: AsyncClient):
    """Test login with invalid username."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "nonexistent",
            "password": "password123"
        }
    )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, admin_user):
    """Test login with invalid password."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, admin_user, test_db):
    """Test login with inactive user."""
    # Deactivate user
    admin_user.is_active = False
    await test_db.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert response.status_code == 401
    assert "Inactive user" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, admin_token):
    """Test getting current user information."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_get_current_user_no_token(client: AsyncClient):
    """Test getting current user without token."""
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test getting current user with invalid token."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_change_password_success(client: AsyncClient, admin_token):
    """Test successful password change."""
    response = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "current_password": "admin123",
            "new_password": "newpassword123"
        }
    )

    assert response.status_code == 200
    assert "Password updated successfully" in response.json()["message"]

    # Test login with new password
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "newpassword123"
        }
    )
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(client: AsyncClient, admin_token):
    """Test password change with wrong current password."""
    response = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        }
    )

    assert response.status_code == 401
    assert "Incorrect current password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_change_password_no_auth(client: AsyncClient):
    """Test password change without authentication."""
    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "admin123",
            "new_password": "newpassword123"
        }
    )

    assert response.status_code == 403
