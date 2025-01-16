from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
import aioredis
import json
import logging

from src.core.agentverse.memory.backends.cache.base import (
    CacheBackend,
    CacheConfig
)
from src.core.agentverse.exceptions import BackendError

logger = logging.getLogger(__name__)

class RedisConfig(CacheConfig):
    """Redis backend configuration"""
    url: str = "redis://localhost:6379"
    db: int = 0
    prefix: str = "agentverse:"
    ttl: int = 3600  # 1 hour default TTL
    max_connections: int = 10
    encoding: str = "utf-8"

class RedisBackend(CacheBackend):
    """Redis cache backend"""
    
    def __init__(self, *args, **kwargs):
        """Initialize Redis backend"""
        super().__init__(*args, **kwargs)
        self.config: RedisConfig = (
            self.config 
            if isinstance(self.config, RedisConfig)
            else RedisConfig(**self.config.model_dump())
        )
        self._client = None
    
    async def connect(self) -> None:
        """Connect to Redis"""
        try:
            self._client = await aioredis.from_url(
                self.config.url,
                db=self.config.db,
                max_connections=self.config.max_connections,
                encoding=self.config.encoding
            )
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            raise BackendError(
                message=f"Failed to connect to Redis: {str(e)}"
            )
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self._client:
            await self._client.close()
    
    async def get(
        self,
        key: str,
        **kwargs
    ) -> Optional[Any]:
        """Get value from Redis
        
        Args:
            key: Cache key
            **kwargs: Additional arguments
            
        Returns:
            Cached value or None
        """
        try:
            # Add prefix
            key = f"{self.config.prefix}{key}"
            
            # Get value
            value = await self._client.get(key)
            
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.error(f"Redis get failed: {str(e)}")
            raise BackendError(
                message=f"Failed to get from Redis: {str(e)}"
            )
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        **kwargs
    ) -> bool:
        """Set value in Redis
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL in seconds
            **kwargs: Additional arguments
            
        Returns:
            Success status
        """
        try:
            # Add prefix
            key = f"{self.config.prefix}{key}"
            
            # Serialize value
            value = json.dumps(value)
            
            # Set with TTL
            await self._client.set(
                key,
                value,
                ex=ttl or self.config.ttl
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Redis set failed: {str(e)}")
            raise BackendError(
                message=f"Failed to set in Redis: {str(e)}"
            )
    
    async def delete(
        self,
        key: str,
        **kwargs
    ) -> bool:
        """Delete value from Redis
        
        Args:
            key: Cache key
            **kwargs: Additional arguments
            
        Returns:
            Success status
        """
        try:
            # Add prefix
            key = f"{self.config.prefix}{key}"
            
            # Delete key
            await self._client.delete(key)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis delete failed: {str(e)}")
            raise BackendError(
                message=f"Failed to delete from Redis: {str(e)}"
            )
    
    async def clear(self) -> bool:
        """Clear Redis cache
        
        Returns:
            Success status
        """
        try:
            # Get all keys with prefix
            pattern = f"{self.config.prefix}*"
            keys = await self._client.keys(pattern)
            
            if keys:
                await self._client.delete(*keys)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis clear failed: {str(e)}")
            raise BackendError(
                message=f"Failed to clear Redis: {str(e)}"
            )
    
    async def exists(
        self,
        key: str,
        **kwargs
    ) -> bool:
        """Check if key exists in Redis
        
        Args:
            key: Cache key
            **kwargs: Additional arguments
            
        Returns:
            Existence status
        """
        try:
            # Add prefix
            key = f"{self.config.prefix}{key}"
            
            # Check existence
            return await self._client.exists(key) > 0
            
        except Exception as e:
            logger.error(f"Redis exists check failed: {str(e)}")
            raise BackendError(
                message=f"Failed to check existence in Redis: {str(e)}"
            ) 