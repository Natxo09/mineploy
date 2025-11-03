"""
Tests for user management endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_users_admin(client: AsyncClient, admin_token, admin_user, moderator_user):
    """Test listing all users as admin."""
    response = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # At least admin and moderator


@pytest.mark.asyncio
async def test_list_users_non_admin(client: AsyncClient, moderator_token):
    """Test listing users as non-admin (should fail)."""
    response = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {moderator_token}"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_users_no_auth(client: AsyncClient):
    """Test listing users without authentication."""
    response = await client.get("/api/v1/users")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_user_by_id(client: AsyncClient, admin_token, admin_user):
    """Test getting user by ID."""
    response = await client.get(
        f"/api/v1/users/{admin_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == admin_user.id
    assert data["username"] == admin_user.username


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient, admin_token):
    """Test getting non-existent user."""
    response = await client.get(
        "/api/v1/users/99999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_user_admin(client: AsyncClient, admin_token):
    """Test creating a new user as admin."""
    response = await client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "role": "viewer"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "viewer"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_create_user_duplicate_username(client: AsyncClient, admin_token, admin_user):
    """Test creating user with duplicate username."""
    response = await client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "admin",
            "email": "another@example.com",
            "password": "password123",
            "role": "viewer"
        }
    )

    assert response.status_code == 400
    assert "Username already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient, admin_token, admin_user):
    """Test creating user with duplicate email."""
    response = await client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "anotheruser",
            "email": "admin@test.com",  # Same email as admin_user
            "password": "password123",
            "role": "viewer"
        }
    )

    assert response.status_code == 400
    assert "Email already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_user_non_admin(client: AsyncClient, moderator_token):
    """Test creating user as non-admin (should fail)."""
    response = await client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {moderator_token}"},
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "role": "viewer"
        }
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient, admin_token, moderator_user):
    """Test updating user information."""
    response = await client.put(
        f"/api/v1/users/{moderator_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "updated_moderator",
            "email": "updated@example.com"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "updated_moderator"
    assert data["email"] == "updated@example.com"


@pytest.mark.asyncio
async def test_update_user_role(client: AsyncClient, admin_token, viewer_user):
    """Test updating user role."""
    response = await client.put(
        f"/api/v1/users/{viewer_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "role": "moderator"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "moderator"


@pytest.mark.asyncio
async def test_update_user_deactivate(client: AsyncClient, admin_token, viewer_user):
    """Test deactivating a user."""
    response = await client.put(
        f"/api/v1/users/{viewer_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "is_active": False
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_update_user_not_found(client: AsyncClient, admin_token):
    """Test updating non-existent user."""
    response = await client.put(
        "/api/v1/users/99999",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "newname"
        }
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, admin_token, viewer_user):
    """Test deleting a user."""
    response = await client.delete(
        f"/api/v1/users/{viewer_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 204

    # Verify user is deleted
    get_response = await client.get(
        f"/api/v1/users/{viewer_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_self(client: AsyncClient, admin_token, admin_user):
    """Test deleting own account (should fail)."""
    response = await client.delete(
        f"/api/v1/users/{admin_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 400
    assert "Cannot delete your own account" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_user_not_found(client: AsyncClient, admin_token):
    """Test deleting non-existent user."""
    response = await client.delete(
        "/api/v1/users/99999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_me_endpoint(client: AsyncClient, moderator_token):
    """Test /users/me endpoint."""
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {moderator_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "moderator"
    assert data["role"] == "moderator"
