import pytest
import asyncio
from redlock import AsyncRedlock

MASTERS = [
    "redis://localhost:6379/0",
    "redis://localhost:6380/0",
    "redis://localhost:6381/0",
    "redis://localhost:6382/0",
    "redis://localhost:6383/0",
]

@pytest.fixture
async def async_redlock():
    return AsyncRedlock(MASTERS)

@pytest.mark.asyncio
async def test_async_acquire_release(async_redlock):
    resource = "test:async:lock:1"
    ttl = 2000
    
    async with async_redlock.lock(resource, ttl) as lock:
        assert lock.valid
        assert lock.resource == resource
        
        # Test mutual exclusion
        lock2 = await async_redlock.acquire(resource, ttl)
        assert lock2 is None

    # Should be released now
    lock3 = await async_redlock.acquire(resource, ttl)
    assert lock3 is not None
    await async_redlock.release(lock3)
