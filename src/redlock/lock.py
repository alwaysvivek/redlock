import asyncio
import random
import time
from types import TracebackType
from typing import Optional, Union

from .algorithm import (
    calculate_drift,
    calculate_validity,
    current_time_ms,
    get_random_token,
)
from .client import AsyncRedlockClient, RedlockConfig, SyncRedlockClient
from .scripts import EXTEND_SCRIPT, RELEASE_SCRIPT


class Lock:
    """Represents a distributed lock."""
    def __init__(self, resource: str, val: str, validity: int, client: Union['Redlock', 'AsyncRedlock']):
        self.resource = resource
        self.value = val
        self.validity = validity
        self.client = client
        self.valid = True

class Redlock:
    """Synchronous Redlock Implementation."""
    
    def __init__(
        self,
        config: Union[RedlockConfig, list[str]],
        retry_count: int = 3,
        retry_delay_min: float = 0.1,
        retry_delay_max: float = 0.3,
    ):
        self.client = SyncRedlockClient(config)
        self.retry_count = retry_count
        self.retry_delay_min = retry_delay_min
        self.retry_delay_max = retry_delay_max

    def lock(self, resource: str, ttl: int, blocking: bool = False) -> 'LockContext':
        return LockContext(self, resource, ttl, blocking)

    def acquire(self, resource: str, ttl: int, blocking: bool = False) -> Optional[Lock]:
        token = get_random_token()
        drift = calculate_drift(ttl)
        
        # Use a while loop to handle blocking mode
        attempt = 0
        while True:
            attempt += 1
            start_time = current_time_ms()
            n_acquired = 0
            
            for instance in self.client.instances:
                try:
                    # set(name, value, px=milliseconds, nx=True)
                    if instance.set(resource, token, px=ttl, nx=True):
                        n_acquired += 1
                except Exception:
                    # Network error, move to next
                    continue
            
            elapsed = current_time_ms() - start_time
            validity = calculate_validity(ttl, elapsed, drift)
            
            if n_acquired >= self.client.quorum and validity > 0:
                return Lock(resource, token, validity, self)
            else:
                # Failed, unlock all
                self._unlock_all(resource, token)
                
                # Check exit conditions
                if not blocking and attempt > self.retry_count:
                    return None
                    
                # Wait before retry
                # Jitter is mandatory for Redlock safety (thundering herd), but customizable
                delay = random.uniform(self.retry_delay_min, self.retry_delay_max)
                time.sleep(delay)


    def release(self, lock: Union[Lock, tuple[str, str]]) -> None:
        """Release a lock. Accepts a Lock object or a (resource, token) tuple."""
        if isinstance(lock, Lock):
            self._unlock_all(lock.resource, lock.value)
            lock.valid = False
        elif isinstance(lock, tuple):
            self._unlock_all(lock[0], lock[1])
            
    def unlock(self, resource: str, token: str) -> None:
        """Explicitly unlock a resource by token."""
        self._unlock_all(resource, token)


    def extend(self, lock: Lock, additional_ttl: int) -> bool:
        """Extend the lock by additional_ttl milliseconds."""
        if not lock.valid:
             return False
        
        n_extended = 0
        for instance in self.client.instances:
            try:
                # eval(script, numkeys, *keys_and_args)
                if instance.eval(EXTEND_SCRIPT, 1, lock.resource, lock.value, additional_ttl): # type: ignore
                   n_extended += 1
            except Exception:
                continue
        
        # Extension is valid if quorum reached again (simplification of algorithm, strictly we should re-check time)
        # But for extension, usually simple quorum set is sufficient as long as we held it.
        return n_extended >= self.client.quorum

    def _unlock_all(self, resource: str, token: str) -> None:
        for instance in self.client.instances:
            try:
                instance.eval(RELEASE_SCRIPT, 1, resource, token) # type: ignore
            except Exception:
                pass


class LockContext:
    """Context Manager for Synchronous Redlock."""
    def __init__(self, redlock: Redlock, resource: str, ttl: int, blocking: bool = False):
        self.redlock = redlock
        self.resource = resource
        self.ttl = ttl
        self.blocking = blocking
        self.lock_obj: Optional[Lock] = None

    def __enter__(self) -> Lock:
        self.lock_obj = self.redlock.acquire(self.resource, self.ttl, blocking=self.blocking)
        if self.lock_obj:
            return self.lock_obj
        # Return an invalid lock object instead of None to prevent AttributeError in 'with' block
        # Users should check lock.valid
        invalid_lock = Lock(self.resource, "", 0, self.redlock)
        invalid_lock.valid = False
        return invalid_lock

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self.lock_obj and self.lock_obj.valid:
            self.redlock.release(self.lock_obj)


class AsyncRedlock:
    """Asynchronous Redlock Implementation."""
    
    def __init__(
        self,
        config: Union[RedlockConfig, list[str]],
        retry_count: int = 3,
        retry_delay_min: float = 0.1,
        retry_delay_max: float = 0.3,
    ):
        self.client = AsyncRedlockClient(config)
        self.retry_count = retry_count
        self.retry_delay_min = retry_delay_min
        self.retry_delay_max = retry_delay_max

    def lock(self, resource: str, ttl: int, blocking: bool = False) -> 'AsyncLockContext':
        return AsyncLockContext(self, resource, ttl, blocking)

    async def acquire(self, resource: str, ttl: int, blocking: bool = False) -> Optional[Lock]:
        token = get_random_token()
        drift = calculate_drift(ttl)
        
        attempt = 0
        while True:
            attempt += 1
            start_time = current_time_ms()
            n_acquired = 0
            
            # Send requests in parallel (multiplexing) as per recommendation
            futures = []
            for instance in self.client.instances:
                 futures.append(instance.set(resource, token, px=ttl, nx=True))
            
            results = await asyncio.gather(*futures, return_exceptions=True)
            
            for res in results:
                if res is True: # set returns True on success
                    n_acquired += 1
            
            elapsed = current_time_ms() - start_time
            validity = calculate_validity(ttl, elapsed, drift)
            
            if n_acquired >= self.client.quorum and validity > 0:
                # We need to adapt Lock to be async-aware or wrapper? 
                # Actually Lock object is just data, we pass 'self' (AsyncRedlock) to it.
                return Lock(resource, token, validity, self)
            else:
                await self._unlock_all(resource, token)
                
                if not blocking and attempt > self.retry_count:
                    return None

                delay = random.uniform(self.retry_delay_min, self.retry_delay_max)
                await asyncio.sleep(delay)
            
        return None


    async def release(self, lock: Union[Lock, tuple[str, str]]) -> None:
        if isinstance(lock, Lock):
            await self._unlock_all(lock.resource, lock.value)
            lock.valid = False
        elif isinstance(lock, tuple):
            await self._unlock_all(lock[0], lock[1])
            
    async def unlock(self, resource: str, token: str) -> None:
         await self._unlock_all(resource, token)

    async def _unlock_all(self, resource: str, token: str) -> None:
        futures = []
        for instance in self.client.instances:
            futures.append(instance.eval(RELEASE_SCRIPT, 1, resource, token)) # type: ignore
        
        await asyncio.gather(*futures, return_exceptions=True)

class AsyncLockContext:
    """Context Manager for Asynchronous Redlock."""
    def __init__(self, redlock: AsyncRedlock, resource: str, ttl: int, blocking: bool = False):
        self.redlock = redlock
        self.resource = resource
        self.ttl = ttl
        self.blocking = blocking
        self.lock_obj: Optional[Lock] = None

    async def __aenter__(self) -> Lock:
        self.lock_obj = await self.redlock.acquire(self.resource, self.ttl, blocking=self.blocking)
        if self.lock_obj:
            return self.lock_obj
        invalid_lock = Lock(self.resource, "", 0, self.redlock)
        invalid_lock.valid = False
        return invalid_lock

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self.lock_obj and self.lock_obj.valid:
            await self.redlock.release(self.lock_obj)
