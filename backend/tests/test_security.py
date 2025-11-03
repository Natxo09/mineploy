"""
Tests for security utilities.
"""

import pytest
from core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
    verify_token,
    generate_rcon_password,
)


def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password_123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)


def test_password_hash_unique():
    """Test that same password generates different hashes."""
    password = "test_password_123"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    # Hashes should be different due to salt
    assert hash1 != hash2
    # But both should verify
    assert verify_password(password, hash1)
    assert verify_password(password, hash2)


def test_create_access_token():
    """Test JWT token creation."""
    data = {"sub": "123"}
    token = create_access_token(data)

    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_token():
    """Test JWT token decoding."""
    data = {"sub": "123", "username": "testuser"}
    token = create_access_token(data)
    decoded = decode_access_token(token)

    assert decoded is not None
    assert decoded["sub"] == "123"
    assert decoded["username"] == "testuser"
    assert "exp" in decoded


def test_decode_invalid_token():
    """Test decoding invalid token."""
    invalid_token = "invalid.token.here"
    decoded = decode_access_token(invalid_token)

    assert decoded is None


def test_verify_token():
    """Test token verification and user ID extraction."""
    user_id = "456"
    token = create_access_token({"sub": user_id})
    extracted_id = verify_token(token)

    assert extracted_id == user_id


def test_verify_invalid_token():
    """Test verification of invalid token."""
    invalid_token = "invalid.token.here"
    result = verify_token(invalid_token)

    assert result is None


def test_generate_rcon_password():
    """Test RCON password generation."""
    password1 = generate_rcon_password()
    password2 = generate_rcon_password()

    assert len(password1) == 32
    assert len(password2) == 32
    assert password1 != password2  # Should be unique
    assert password1.isalnum()  # Should only contain letters and numbers


def test_generate_rcon_password_custom_length():
    """Test RCON password generation with custom length."""
    password = generate_rcon_password(length=16)

    assert len(password) == 16
    assert password.isalnum()
