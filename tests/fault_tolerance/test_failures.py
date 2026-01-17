
import pytest
import requests
from redlock import Redlock

# Toxiproxy API
TOXIPROXY_API = "http://localhost:8474"

# Use the PROXY ports defined in docker-compose for the client
# Redis 1-5 are proxied at 26379-26383
PROXY_MASTERS = [
    "redis://localhost:26379/0",
    "redis://localhost:26380/0",
    "redis://localhost:26381/0",
    "redis://localhost:26382/0",
    "redis://localhost:26383/0",
]

# Mapping to Toxiproxy proxy names (must match docker-compose service names usually, 
# but Toxiproxy creates proxies dynamically or via config. 
# We need to Configure Toxiproxy first or assume they exist?
# The docker image 'ghcr.io/shopify/toxiproxy' starts empty. We must populate it.
# Actually, we can configure it in a fixture.

@pytest.fixture(scope="module", autouse=True)
def setup_toxiproxy():
    """Setup toxiproxy proxies mapping ports 26379+ to redis-X:6379"""
    proxies = []
    for i in range(1, 6):
        name = f"redis_{i}"
        upstream = f"redis-{i}:6379"
        listen = f"0.0.0.0:263{78+i}" # 26379, 26380...
        
        payload = {
            "name": name,
            "listen": listen,
            "upstream": upstream,
            "enabled": True
        }
        
        try:
            # Delete if exists
            requests.delete(f"{TOXIPROXY_API}/proxies/{name}")
        except Exception:
            pass
            
        # Create
        resp = requests.post(f"{TOXIPROXY_API}/proxies", json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(f"Failed to create proxy {name}: {resp.text}")
        print(f"DEBUG: Created {name} - {resp.status_code}")
        
    all_proxies = requests.get(f"{TOXIPROXY_API}/proxies").json()
    print(f"DEBUG: Current Proxies: {all_proxies.keys()}")
    proxies.append(name)
        
    yield proxies
    
    # Cleanup
    for name in proxies:
         requests.delete(f"{TOXIPROXY_API}/proxies/{name}")

def disable_proxy(name):
    # Update the proxy to set enabled=False
    resp = requests.post(f"{TOXIPROXY_API}/proxies/{name}", json={"enabled": False})
    resp.raise_for_status()

def enable_proxy(name):
    # Update the proxy to set enabled=True
    resp = requests.post(f"{TOXIPROXY_API}/proxies/{name}", json={"enabled": True})
    resp.raise_for_status()


def test_split_brain_majority_available():
    """
    Test acquiring lock when 2 out of 5 nodes are down (Majority 3/5 still up).
    Should SUCCEED.
    """
    redlock = Redlock(PROXY_MASTERS)
    
    # Kill 2 nodes (redis_1, redis_2)
    disable_proxy("redis_1")
    disable_proxy("redis_2")
    
    try:
        resource = "test:splitbrain:success"
        lock = redlock.acquire(resource, ttl=2000)
        
        # Should succeed because 3 nodes are still up (Quorum = 3)
        assert lock is not None
        assert lock.valid
        
        redlock.release(lock)
        
    finally:
        # Restore
        enable_proxy("redis_1")
        enable_proxy("redis_2")


def test_split_brain_minority_available():
    """
    Test acquiring lock when 3 out of 5 nodes are down (Only 2/5 up).
    Should FAIL.
    """
    redlock = Redlock(PROXY_MASTERS, retry_count=1) # Don't retry too much
    
    # Kill 3 nodes
    disable_proxy("redis_1")
    disable_proxy("redis_2")
    disable_proxy("redis_3")
    
    try:
        resource = "test:splitbrain:fail"
        lock = redlock.acquire(resource, ttl=2000)
        
        # Should fail
        assert lock is None
        
    finally:
        enable_proxy("redis_1")
        enable_proxy("redis_2")
        enable_proxy("redis_3")
