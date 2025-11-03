"""
Security utilities for authentication and authorization.
Handles JWT tokens, password hashing, and user verification.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password
        hashed_password: The hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password

    Returns:
        The hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary with data to encode in token (typically {"sub": user_id})
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            hours=settings.jwt_expiration_hours
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT access token.

    Args:
        token: The JWT token string

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str) -> Optional[str]:
    """
    Verify token and extract user ID.

    Args:
        token: The JWT token string

    Returns:
        User ID (sub claim) if token is valid, None otherwise
    """
    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id: Optional[str] = payload.get("sub")
    return user_id


def create_refresh_token() -> str:
    """
    Create a secure random refresh token.

    Returns:
        Random token string (64 characters)
    """
    import secrets
    return secrets.token_urlsafe(48)  # Generates ~64 characters


def generate_rcon_password(length: int = 32) -> str:
    """
    Generate a secure random password for RCON.

    Args:
        length: Length of the password (default: 32)

    Returns:
        Random password string
    """
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password
