from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

class RedlockConfig(BaseModel):
    """Configuration for Redlock clients."""
    masters: List[str] = Field(
        ..., 
        description="List of Redis connection URLs (e.g., redis://localhost:6379/0)"
    )
    socket_timeout: float = Field(0.1, description="Socket timeout in seconds")
    socket_connect_timeout: float = Field(0.1, description="Connect timeout in seconds")

class RedlockClientBase:
    """Base client holding configuration."""
    def __init__(self, config: RedlockConfig):
        self.config = config
        self.quorum = (len(config.masters) // 2) + 1

class SyncRedlockClient(RedlockClientBase):
    """Synchronous Redlock Client."""
    def __init__(self, config: Union[RedlockConfig, List[str], List[Redis]]):
        if isinstance(config, list):
             # Basic heuristic: if items are strings, treat as URLs
             # If items are Redis objects, use them directly
            if config and isinstance(config[0], str):
                 config = RedlockConfig(masters=config) # type: ignore
            elif config and isinstance(config[0], Redis):
                 # Handle list of existing clients case if needed, but for now strict config
                 # We'll assume list of strings for simplicity or Config object
                 pass

        # If simple list of strings passed (convenience)
        if isinstance(config, list) and all(isinstance(x, str) for x in config):
            config = RedlockConfig(masters=config) # type: ignore

        if not isinstance(config, RedlockConfig):
             raise ValueError("Config must be RedlockConfig or list of strings")

        super().__init__(config)
        self.instances: List[Redis] = []
        for url in self.config.masters:
            client = Redis.from_url(
                url, 
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout
            )
            self.instances.append(client)

class AsyncRedlockClient(RedlockClientBase):
    """Asynchronous Redlock Client."""
    def __init__(self, config: Union[RedlockConfig, List[str]]):
        # Convenience: Allow passing list of strings directly
        if isinstance(config, list):
            config = RedlockConfig(masters=config)

        super().__init__(config)
        self.instances: List[AsyncRedis] = []
        for url in self.config.masters:
            client = AsyncRedis.from_url(
                url,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout
            )
            self.instances.append(client)
