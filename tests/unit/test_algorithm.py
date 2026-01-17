from redlock.algorithm import calculate_drift, calculate_validity, get_quorum


def test_quorum_calculation():
    assert get_quorum(1) == 1  # 0 + 1
    assert get_quorum(2) == 2  # 1 + 1 (requires unanimous? No, n//2 + 1. 2//2 = 1 + 1 = 2)
    assert get_quorum(3) == 2  # 1 + 1
    assert get_quorum(5) == 3  # 2 + 1

def test_drift_calculation():
    # 2% drift + 2ms
    # 10000 * 0.01 = 100
    # 100 + 2 = 102
    assert calculate_drift(10000, 0.01) == 102

def test_validity_calculation():
    ttl = 10000
    elapsed = 50
    drift = 102
    # 10000 - 50 - 102 = 9848
    assert calculate_validity(ttl, elapsed, drift) == 9848

def test_validity_expired():
    # Only 100ms TTL
    ttl = 100
    elapsed = 50
    drift = 60 # huge drift
    # 100 - 50 - 60 = -10 (Expired)
    assert calculate_validity(ttl, elapsed, drift) < 0
