from hypothesis import given, strategies as st
from redlock.algorithm import calculate_drift, calculate_validity

@given(
    ttl=st.integers(min_value=100, max_value=60000),
    drift_factor=st.floats(min_value=0.0, max_value=0.1)
)
def test_fuzz_drift_calculation(ttl, drift_factor):
    """Fuzz test drift calculation to ensure it's always positive and reasonable."""
    drift = calculate_drift(ttl, drift_factor)
    
    # Drift should always be > 0 (at least 2ms constant)
    assert drift >= 2
    
    # Drift should be roughly the percentage requested
    expected_drift_part = int(ttl * drift_factor)
    assert drift == expected_drift_part + 2

@given(
    ttl=st.integers(min_value=1000, max_value=10000),
    elapsed=st.integers(min_value=0, max_value=15000),
)
def test_fuzz_validity(ttl, elapsed):
    """
    Fuzz locking validity. 
    1. If elapsed > TTL, validity should be < 0 (or close to it depending on drift).
    2. Logic consistency check.
    """
    drift = calculate_drift(ttl)
    validity = calculate_validity(ttl, elapsed, drift)
    
    if elapsed >= ttl:
        # It must be expired
        assert validity < 0
    elif elapsed + drift < ttl:
        # It must be valid
        assert validity > 0
