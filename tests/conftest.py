
import asyncio
import pytest
from typing import Generator

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db():
    """Setup and teardown database connection."""
    from tabernacleorm import connect, disconnect
    # Use in-memory SQLite for fast testing
    conn = await connect("sqlite:///:memory:").connect()
    yield conn
    await disconnect()
