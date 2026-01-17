import time
import uuid

# Redis documentation specifies 0.01 (1%) clock drift
DEFAULT_CLOCK_DRIFT_FACTOR = 0.01

def get_random_token() -> str:
    """Generate a unique random token for locking."""
    return str(uuid.uuid4())

def get_quorum(n: int) -> int:
    """Calculate the quorum size needed for N masters."""
    return (n // 2) + 1

def calculate_drift(ttl: int, clock_drift_factor: float = DEFAULT_CLOCK_DRIFT_FACTOR) -> int:
    """
    Calculate lock validity drift.
    
    Drift = (TTL * clock_drift_factor) + 2 milliseconds
    The 2ms constant compensates for the process execution time and network latency
    margin of error.
    """
    return int(ttl * clock_drift_factor) + 2

def calculate_validity(ttl: int, elapsed_time_ms: int, drift: int) -> int:
    """
    Calculate the remaining validity time of the lock.
    
    Validity = TTL - Elapsed Time - Drift
    """
    return ttl - elapsed_time_ms - drift

def current_time_ms() -> int:
    """Get current time in milliseconds."""
    return int(time.time() * 1000)
