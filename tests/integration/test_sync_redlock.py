import time

import pytest
from redlock import Redlock

# Assuming docker-compose is running
MASTERS = [
    "redis://localhost:6379/0",
    "redis://localhost:6380/0",
    "redis://localhost:6381/0",
    "redis://localhost:6382/0",
    "redis://localhost:6383/0",
]

@pytest.fixture
def redlock():
    return Redlock(MASTERS)

def test_acquire_release(redlock):
    resource = "test:lock:1"
    ttl = 2000
    
    with redlock.lock(resource, ttl) as lock:
        assert lock.valid
        assert lock.resource == resource
        assert lock.validity > 0
        
        # Verify mutual exclusion
        lock2 = redlock.acquire(resource, ttl)
        assert lock2 is None, "Should not optimize acquire lock on same resource"

    # After exit, should be released
    lock3 = redlock.acquire(resource, ttl)
    assert lock3 is not None
    assert lock3.valid
    redlock.release(lock3)

def test_lock_expiration(redlock):
    resource = "test:lock:expire"
    ttl = 1000
    
    lock = redlock.acquire(resource, ttl)
    assert lock is not None
    assert lock.valid
    
    # Wait for expiration
    time.sleep(1.2)
    
    # Try to acquire again - should succeed because previous expired
    lock2 = redlock.acquire(resource, ttl)
    assert lock2 is not None
    assert lock2.valid
    
    redlock.release(lock2)
