# Redlock-py

[![PyPI version](https://badge.fury.io/py/redlock-py.svg)](https://badge.fury.io/py/redlock-py)
[![CI](https://github.com/alwaysvivek/redlock-py/actions/workflows/ci.yml/badge.svg)](https://github.com/alwaysvivek/redlock-py/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A **production-grade**, type-safe, and modern implementation of the [Redis Redlock](https://redis.io/docs/manual/patterns/distributed-locks/) algorithm in Python. Supports both **Synchronous** and **Asynchronous** (asyncio) execution.

---

## 🏗 Architecture

The `Redlock` client manages connections to `N` independent Redis instances. To acquire a lock, it attempts to set a unique token on all instances sequentially. The lock is considered acquired only if:
1.  Quorum (N/2 + 1) instances allow the lock.
2.  Total time taken is less than the lock validity time.

```mermaid
sequenceDiagram
    participant Client
    participant R1 as Redis 1
    participant R2 as Redis 2
    participant R3 as Redis 3 (Quorum)
    participant R4 as Redis 4 
    participant R5 as Redis 5

    Client->>R1: SET resource unique_token NX PX 10000
    R1-->>Client: OK
    Client->>R2: SET resource unique_token NX PX 10000
    R2-->>Client: OK
    Client->>R3: SET resource unique_token NX PX 10000
    R3-->>Client: OK
    
    Note over Client: Quorum reached (3/5)
    
    Client-->>Client: Calculate Drift & Validity
    
    alt Success
        Client->>Client: Return Valid Lock
    else Failure (timeout or no quorum)
        Client->>R1: DEL resource (Unlock)
        Client->>R2: DEL resource (Unlock)
        Client->>R3: DEL resource (Unlock)
    end
```

## 🚀 Features

*   **Dual Interface**: Complete support for `Redlock` (blocking/sync) and `AsyncRedlock` (async/await).
*   **Type Safe**: 100% typed with `mypy --strict`.
*   **Fault Tolerant**: Resilient to single node failures.
*   **Production Ready**: Includes Jitter, Drift calculation, and proper error handling.

## 📦 Installation

```bash
pip install redlock-py
# or with poetry
poetry add redlock-py
```

## 💻 Usage

### Synchronous

```python
from redlock import Redlock, RedlockConfig

# Configure with list of Redis URIs
config = RedlockConfig(
    masters=[
        "redis://localhost:6379/0",
        "redis://localhost:6380/0",
        "redis://localhost:6381/0",
    ]
)

lock_manager = Redlock(config)

# 1. Standard usage (Non-blocking)
try:
    with lock_manager.lock("my-resource", ttl=10000) as lock:
        if lock.valid:
            print(f"Lock acquired: {lock.resource}")
            # Do critical work...
        else:
            print("Failed to acquire lock")
except Exception:
    pass

# 2. Blocking usage (Wait indefinitely until acquired)
with lock_manager.lock("my-resource", ttl=10000, blocking=True) as lock:
    print("Locked! This might have waited.")

# 3. Explicit Token Unlock (e.g. from a different process)
lock_manager.unlock("my-resource", "previous-token-uuid")
```

### Asynchronous

```python
import asyncio
from redlock import AsyncRedlock, RedlockConfig

async def main():
    config = RedlockConfig(
        masters=[
            "redis://localhost:6379/0",
            "redis://localhost:6380/0",
            "redis://localhost:6381/0",
        ]
    )
    
    lock_manager = AsyncRedlock(config)

    async with lock_manager.lock("my-async-resource", ttl=10000) as lock:
        if lock.valid:
            print("Async lock acquired!")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🧪 Testing

This project uses a rigorous testing strategy including:
1.  **Unit Tests**: Mocked Redis interactions.
2.  **Integration Tests**: Docker-based tests against 5 real Redis nodes.
3.  **Fault Injection**: Network partition simulations using Toxiproxy.

To run tests:
```bash
docker-compose up -d
pytest
```
