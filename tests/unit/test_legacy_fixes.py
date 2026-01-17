from unittest.mock import MagicMock

import pytest
from redlock.lock import Redlock
from redlock.scripts import RELEASE_SCRIPT


@pytest.fixture
def mock_client(mocker):
    """Mock the Redis client instances."""
    mock_redis = MagicMock()
    # Mock set to return True by default (acquired)
    mock_redis.set.return_value = True
    
    # Mock eval for release to return 1 (success)
    mock_redis.eval.return_value = 1
    
    # Create Redlock with mocked client instances
    redlock = Redlock(["redis://localhost:6379/0"])
    # Bypass client creation and inject mock
    redlock.client.instances = [mock_redis]
    # Set quorum for single instance
    redlock.client.quorum = 1
    
    return redlock, mock_redis

def test_retry_count_zero(mock_client):
    """Test that retry_count=0 still tries at least once."""
    redlock, mock_redis = mock_client
    redlock.retry_count = 0
    
    # Reset mock to verify call count
    mock_redis.set.reset_mock()
    
    redlock.acquire("resource", 1000)
    
    # Should be called exactly once
    assert mock_redis.set.call_count == 1

def test_retry_count_logic(mock_client):
    """Test that retry_count=3 tries 4 times total (1 try + 3 retries)."""
    redlock, mock_redis = mock_client
    redlock.retry_count = 3
    # Make it fail always
    mock_redis.set.return_value = False
    
    redlock.acquire("resource", 1000)
    
    # Should be called 4 times due to loop: attempt 1, 2, 3, 4
    assert mock_redis.set.call_count == 4

def test_unlock_by_token(mock_client):
    """Test explicit unlock using resource and token string."""
    redlock, mock_redis = mock_client
    resource = "test:resource"
    token = "abc-123-token"
    
    redlock.unlock(resource, token)
    
    # Verify Lua script call
    mock_redis.eval.assert_called_with(RELEASE_SCRIPT, 1, resource, token)

def test_blocking_acquisition(mock_client):
    """Test blocking=True retries beyond retry_count."""
    redlock, mock_redis = mock_client
    redlock.retry_count = 1
    redlock.retry_delay_min = 0.01
    redlock.retry_delay_max = 0.01
    
    # Fail 3 times, then succeed
    # retry_count=1 means normally it would try 2 times (initial + 1 retry) and fail.
    # We want to prove it goes to a 3rd time or more.
    mock_redis.set.side_effect = [False, False, True]
    
    lock = redlock.acquire("resource", 1000, blocking=True)
    
    assert lock is not None
    assert lock.valid
    # Should have been called 3 times
    assert mock_redis.set.call_count == 3
