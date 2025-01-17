from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from src.core.infrastructure.db.mongo_client import MongoDBClient
import logging

logger = logging.getLogger(__name__)

class EnvironmentRepository:
    """Repository for environment persistence"""
    
    def __init__(self, mongo_client: MongoDBClient):
        self.collection = mongo_client.db.environments
        
    def _serialize_environment(self, env: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to serializable dict"""
        if not env:
            return None
            
        serialized = dict(env)
        if "_id" in serialized:
            serialized["_id"] = str(serialized["_id"])
            
        serialized.setdefault("id", str(serialized.get("_id")))
        serialized.setdefault("metadata", {})
        
        return serialized
        
    async def create(self, env_data: Dict[str, Any]) -> str:
        """Create new environment"""
        try:
            result = await self.collection.insert_one(env_data)
            return env_data["id"]
        except DuplicateKeyError:
            raise ValueError(f"Environment with name '{env_data['name']}' already exists")
            
    async def get(self, env_id: str) -> Optional[Dict[str, Any]]:
        """Get environment by ID"""
        result = await self.collection.find_one({"id": env_id})
        return self._serialize_environment(result)
        
    async def list_environments(self) -> List[Dict[str, Any]]:
        """List all environments"""
        cursor = self.collection.find({})
        environments = await cursor.to_list(length=None)
        return [self._serialize_environment(env) for env in environments if env]
        
    async def update(self, env_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update environment"""
        result = await self.collection.find_one_and_update(
            {"id": env_id},
            {"$set": update_data},
            return_document=True
        )
        return self._serialize_environment(result)
        
    async def delete(self, env_id: str) -> bool:
        """Delete environment"""
        result = await self.collection.delete_one({"id": env_id})
        return result.deleted_count > 0 