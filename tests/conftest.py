# tests/conftest.py
import asyncio
from typing import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.main import app

# Використовуємо in-memory SQLite для кожного тесту окремо
TEST_DATABASE_URL = "sqlite+aiosqlite://"

# Create async engine for tests
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def setup_database():
    """Create all tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for a test."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(session) -> AsyncGenerator[AsyncClient, None]:
    """Create an HTTP client for testing."""
    
    # Override the database session dependency
    async def override_get_session():
        yield session
    
    from app.database.session import get_session
    app.dependency_overrides[get_session] = override_get_session
    
    # Mock user for auth
    MOCK_USER = type('MockUser', (), {
        'uuid': uuid4(),
        'username': 'testuser',
        'is_active': True,
        'must_change_password': False,
        'role': type('MockRole', (), {
            'uuid': uuid4(),
            'name': 'admin'
        })()
    })
    
    # Override auth dependency
    async def override_get_current_user():
        return MOCK_USER
    
    from app.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# Helper function для створення UUID без використання типу UUID у SQLite
def to_uuid_string(uuid_val):
    """Convert UUID to string for SQLite compatibility."""
    return str(uuid_val)