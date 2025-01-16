"""Connector Factory Module"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import aiohttp
import aiofiles
from pydantic import Field

from src.core.infrastructure.db.mongo_client import MongoDBClient
from src.core.agentverse.message_bus import MessageBus
from src.core.agentverse.factories.base import BaseFactory, FactoryConfig

class ConnectorFactoryConfig(FactoryConfig):
    """Connector factory configuration"""
    connector_type: str = "database"  # database, api, messaging, storage
    connection_params: Dict[str, Any] = Field(default_factory=dict)
    auth_config: Dict[str, Any] = Field(default_factory=dict)
    retry_policy: Dict[str, Any] = Field(default_factory=dict)
    pool_config: Optional[Dict[str, Any]] = None

class ConnectorFactory(BaseFactory):
    """Factory for creating system connectors"""
    
    @classmethod
    async def create(
        cls,
        config: ConnectorFactoryConfig,
        **kwargs
    ) -> Any:
        """Create a connector instance"""
        if not await cls.validate_config(config):
            raise ValueError("Invalid connector configuration")
            
        # Create appropriate connector type
        if config.connector_type == "database":
            return await cls._create_database_connector(config, **kwargs)
        elif config.connector_type == "api":
            return await cls._create_api_connector(config, **kwargs)
        elif config.connector_type == "messaging":
            return await cls._create_messaging_connector(config, **kwargs)
        elif config.connector_type == "storage":
            return await cls._create_storage_connector(config, **kwargs)
        else:
            raise ValueError(f"Unsupported connector type: {config.connector_type}")
    
    @classmethod
    async def validate_config(
        cls,
        config: ConnectorFactoryConfig
    ) -> bool:
        """Validate connector factory configuration"""
        valid_types = ["database", "api", "messaging", "storage"]
        if config.connector_type not in valid_types:
            return False
        if not config.connection_params:
            return False
        return True
    
    @classmethod
    def get_defaults(cls) -> Dict[str, Any]:
        """Get default connector configuration"""
        return {
            "type": "connector",
            "connector_type": "database",
            "connection_params": {},
            "auth_config": {},
            "retry_policy": {
                "max_retries": 3,
                "backoff": "exponential"
            },
            "pool_config": {
                "min_size": 1,
                "max_size": 10
            }
        }
    
    @classmethod
    async def _create_database_connector(cls, config: ConnectorFactoryConfig, **kwargs):
        """Create database connector"""
        conn_params = config.connection_params
        pool_config = config.pool_config or {}
        
        # Create database client
        client = MongoDBClient(
            uri=conn_params.get("uri"),
            database=conn_params.get("database"),
            min_pool_size=pool_config.get("min_size", 1),
            max_pool_size=pool_config.get("max_size", 10)
        )
        
        # Apply authentication if configured
        if config.auth_config:
            await client.authenticate(
                username=config.auth_config.get("username"),
                password=config.auth_config.get("password")
            )
        
        return client
    
    @classmethod
    async def _create_api_connector(cls, config: ConnectorFactoryConfig, **kwargs):
        """Create API connector"""
        conn_params = config.connection_params
        retry_policy = config.retry_policy
        
        # Create session with retry logic
        session = aiohttp.ClientSession(
            base_url=conn_params.get("base_url"),
            headers=conn_params.get("headers", {}),
            timeout=aiohttp.ClientTimeout(total=conn_params.get("timeout", 30))
        )
        
        # Add retry middleware if configured
        if retry_policy:
            from aiohttp_retry import RetryClient
            session = RetryClient(
                client_session=session,
                retry_options={
                    "attempts": retry_policy.get("max_retries", 3),
                    "start_timeout": retry_policy.get("initial_delay", 1),
                    "max_timeout": retry_policy.get("max_delay", 30),
                    "factor": retry_policy.get("backoff_factor", 2)
                }
            )
        
        return session
    
    @classmethod
    async def _create_messaging_connector(cls, config: ConnectorFactoryConfig, **kwargs):
        """Create messaging connector"""
        conn_params = config.connection_params
        
        # Create message bus with configured transport
        bus = MessageBus(
            transport_type=conn_params.get("transport", "memory"),
            host=conn_params.get("host"),
            port=conn_params.get("port"),
            channel_capacity=conn_params.get("channel_capacity", 100),
            delivery_guarantee=conn_params.get("delivery_guarantee", "at_least_once")
        )
        
        # Configure persistence if enabled
        if conn_params.get("persistent", False):
            await bus.enable_persistence(
                storage_path=conn_params.get("storage_path", "./message_store")
            )
        
        return bus
    
    @classmethod
    async def _create_storage_connector(cls, config: ConnectorFactoryConfig, **kwargs):
        """Create storage connector"""
        conn_params = config.connection_params
        
        class StorageConnector:
            def __init__(self, base_path: str, create: bool = True):
                self.base_path = Path(base_path)
                if create:
                    self.base_path.mkdir(parents=True, exist_ok=True)
                    
            async def write(self, path: str, data: bytes) -> None:
                full_path = self.base_path / path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(full_path, 'wb') as f:
                    await f.write(data)
                    
            async def read(self, path: str) -> bytes:
                full_path = self.base_path / path
                async with aiofiles.open(full_path, 'rb') as f:
                    return await f.read()
                    
            async def delete(self, path: str) -> None:
                full_path = self.base_path / path
                if full_path.exists():
                    full_path.unlink()
                    
            async def list(self, path: str = "") -> List[str]:
                full_path = self.base_path / path
                return [str(p.relative_to(self.base_path)) for p in full_path.rglob("*")]
        
        return StorageConnector(
            base_path=conn_params.get("base_path", "./storage"),
            create=conn_params.get("create_path", True)
        ) 