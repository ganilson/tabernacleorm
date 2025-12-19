
import asyncio
import pytest
from typing import Generator

# event_loop fixture removed to use pytest-asyncio default


@pytest.fixture
async def db():
    """Setup and teardown database connection."""
    from tabernacleorm import connect, disconnect
    # Use in-memory SQLite for fast testing
    conn = await connect("sqlite:///:memory:").connect()
    yield conn
    await disconnect()
