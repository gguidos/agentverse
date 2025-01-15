from redis.asyncio import Redis
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    """Class to encapsulate Redis operations."""

    def __init__(self, host: str, port: int, db: int, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.client: Optional[Redis] = None

    async def connect(self) -> None:
        """Connect to the Redis server."""
        if not self.client:
            self.client = await Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info(f"Connected to Redis at {self.host}:{self.port}")

    async def disconnect(self) -> None:
        """Disconnect from the Redis server."""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Redis.")
            self.client = None

    async def get(self, key: str) -> Optional[str]:
        """Get a value from Redis by key."""
        if not self.client:
            raise ConnectionError("Redis client is not connected.")
        return await self.client.get(key)

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """Set a key-value pair in Redis with an optional expiration time."""
        if not self.client:
            raise ConnectionError("Redis client is not connected.")
        return await self.client.set(key, value, ex=expire)

    async def delete(self, key: str) -> int:
        """Delete a key from Redis."""
        if not self.client:
            raise ConnectionError("Redis client is not connected.")
        return await self.client.delete(key)

    async def ping(self) -> bool:
        """Ping the Redis server to check connection status."""
        if not self.client:
            raise ConnectionError("Redis client is not connected.")
        return await self.client.ping() == "PONG"

    def __getattr__(self, name: str):
        """
        Forward attribute lookups to the Redis client.
        This will ensure that methods like `script_load` can be accessed.
        """
        if self.client:
            return getattr(self.client, name)
        raise AttributeError(f"'RedisClient' object has no attribute '{name}'")
