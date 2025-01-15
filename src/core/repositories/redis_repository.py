from src.infrastructure.db.redis_client import RedisClient
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class RedisRepository:
    """Repository to interact with Redis client for data operations."""

    def __init__(self, client: RedisClient):
        self.client = client

    async def get_value(self, key: str) -> Optional[str]:
        """Get a value from Redis by key."""
        try:
            value = await self.client.get(key)
            logger.info(f"Fetched value for key '{key}': {value}")
            return value
        except Exception as e:
            logger.error(f"Error fetching value for key '{key}': {e}")
            raise

    async def set_value(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """Set a key-value pair in Redis with an optional expiration time."""
        try:
            result = await self.client.set(key, value, expire)
            logger.info(f"Set value for key '{key}' with expiration '{expire}': {result}")
            return result
        except Exception as e:
            logger.error(f"Error setting value for key '{key}': {e}")
            raise

    async def delete_value(self, key: str) -> int:
        """Delete a key from Redis."""
        try:
            deleted = await self.client.delete(key)
            logger.info(f"Deleted key '{key}': {deleted}")
            return deleted
        except Exception as e:
            logger.error(f"Error deleting key '{key}': {e}")
            raise

    async def check_connection(self) -> bool:
        """Ping the Redis server to check connection status."""
        try:
            is_connected = await self.client.ping()
            logger.info(f"Redis connection status: {is_connected}")
            return is_connected
        except Exception as e:
            logger.error(f"Error pinging Redis: {e}")
            raise