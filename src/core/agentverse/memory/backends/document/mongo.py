from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import logging

from src.core.agentverse.memory.backends.document.base import (
    DocumentBackend,
    DocumentConfig
)
from src.core.agentverse.exceptions import BackendError

logger = logging.getLogger(__name__)

class MongoConfig(DocumentConfig):
    """MongoDB backend configuration"""
    database: str = "agentverse"
    connection_url: str = "mongodb://localhost:27017"
    connection_timeout: int = 5000

class MongoBackend(DocumentBackend):
    """MongoDB document storage backend"""
    
    def __init__(self, *args, **kwargs):
        """Initialize MongoDB backend"""
        super().__init__(*args, **kwargs)
        self.config: MongoConfig = (
            self.config 
            if isinstance(self.config, MongoConfig)
            else MongoConfig(**self.config.model_dump())
        )
    
    async def connect(self) -> None:
        """Connect to MongoDB"""
        try:
            self._client = AsyncIOMotorClient(
                self.config.connection_url,
                serverSelectionTimeoutMS=self.config.connection_timeout
            )
            db = self._client[self.config.database]
            self._collection = db[self.config.collection]
            
            # Create indexes
            for field in self.config.index_fields:
                await self._collection.create_index(field)
                
        except Exception as e:
            logger.error(f"MongoDB connection failed: {str(e)}")
            raise BackendError(
                message=f"Failed to connect to MongoDB: {str(e)}"
            )
    
    async def disconnect(self) -> None:
        """Disconnect from MongoDB"""
        if self._client:
            self._client.close()
    
    async def store(
        self,
        documents: List[Dict[str, Any]],
        **kwargs
    ) -> List[str]:
        """Store documents in MongoDB"""
        try:
            # Validate documents
            documents = await self._validate_documents(documents)
            
            # Insert documents
            result = await self._collection.insert_many(documents)
            
            return [str(id) for id in result.inserted_ids]
            
        except Exception as e:
            logger.error(f"MongoDB storage failed: {str(e)}")
            raise BackendError(
                message=f"Failed to store documents: {str(e)}"
            )
    
    async def retrieve(
        self,
        query: Dict[str, Any],
        limit: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Retrieve documents from MongoDB"""
        try:
            # Validate query
            query = await self._validate_query(query)
            
            # Execute query
            cursor = self._collection.find(query)
            
            if limit:
                cursor = cursor.limit(limit)
            
            return [doc async for doc in cursor]
            
        except Exception as e:
            logger.error(f"MongoDB retrieval failed: {str(e)}")
            raise BackendError(
                message=f"Failed to retrieve documents: {str(e)}"
            )
    
    async def update(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any],
        **kwargs
    ) -> int:
        """Update documents in MongoDB"""
        try:
            # Validate inputs
            query = await self._validate_query(query)
            if not isinstance(update, dict):
                raise BackendError(
                    message="Invalid update operation",
                    details={"type": type(update)}
                )
            
            # Execute update
            result = await self._collection.update_many(
                query,
                {"$set": update}
            )
            
            return result.modified_count
            
        except Exception as e:
            logger.error(f"MongoDB update failed: {str(e)}")
            raise BackendError(
                message=f"Failed to update documents: {str(e)}"
            )
    
    async def delete(
        self,
        query: Dict[str, Any],
        **kwargs
    ) -> int:
        """Delete documents from MongoDB"""
        try:
            # Validate query
            query = await self._validate_query(query)
            
            # Execute deletion
            result = await self._collection.delete_many(query)
            
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"MongoDB deletion failed: {str(e)}")
            raise BackendError(
                message=f"Failed to delete documents: {str(e)}"
            )
    
    async def clear(self) -> bool:
        """Clear MongoDB collection"""
        try:
            await self._collection.delete_many({})
            return True
            
        except Exception as e:
            logger.error(f"MongoDB clear failed: {str(e)}")
            raise BackendError(
                message=f"Failed to clear collection: {str(e)}"
            ) 