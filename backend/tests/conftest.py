"""
Pytest configuration and fixtures for testing.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from core.database import Base, get_db
from core.config import settings
from main import app


# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database for each test function.
    Uses in-memory SQLite for speed.
    """
    # Create async engine for testing
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=None,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client with a test database session.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(test_db: AsyncSession):
    """Create an admin user for testing."""
    from models.user import User, UserRole
    from core.security import get_password_hash

    user = User(
        username="admin",
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def moderator_user(test_db: AsyncSession):
    """Create a moderator user for testing."""
    from models.user import User, UserRole
    from core.security import get_password_hash

    user = User(
        username="moderator",
        email="moderator@test.com",
        hashed_password=get_password_hash("mod123"),
        role=UserRole.MODERATOR,
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def viewer_user(test_db: AsyncSession):
    """Create a viewer user for testing."""
    from models.user import User, UserRole
    from core.security import get_password_hash

    user = User(
        username="viewer",
        email="viewer@test.com",
        hashed_password=get_password_hash("view123"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user):
    """Generate JWT token for admin user."""
    from core.security import create_access_token

    return create_access_token(data={"sub": str(admin_user.id)})


@pytest.fixture
def moderator_token(moderator_user):
    """Generate JWT token for moderator user."""
    from core.security import create_access_token

    return create_access_token(data={"sub": str(moderator_user.id)})


@pytest.fixture
def viewer_token(viewer_user):
    """Generate JWT token for viewer user."""
    from core.security import create_access_token

    return create_access_token(data={"sub": str(viewer_user.id)})
