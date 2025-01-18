from typing import Dict, Any, Optional, List
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from src.core.infrastructure.db.mongo_client import MongoDBClient
import logging

logger = logging.getLogger(__name__)

class AgentRepository:
    """Repository for agent persistence"""
    
    def __init__(self, mongo_client: MongoDBClient):
        self.client = mongo_client
        self.collection = self.client.db.agents
        
    def _serialize_agent(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to serializable dict"""
        if not agent:
            return None
        
        def convert_objectid(obj):
            if isinstance(obj, dict):
                return {k: convert_objectid(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_objectid(item) for item in obj]
            elif isinstance(obj, ObjectId):
                return str(obj)
            return obj
        
        # Create a copy and convert all ObjectIds to strings
        serialized = convert_objectid(dict(agent))
        
        # Convert primary _id to id
        if '_id' in serialized:
            serialized['id'] = serialized['_id']
            del serialized['_id']
        
        # Use external_id if it exists
        if 'external_id' in serialized:
            serialized['id'] = serialized['external_id']
            del serialized['external_id']
        
        return serialized
        
    async def create(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent"""
        try:
            # Generate new ObjectId instead of using UUID
            agent_data['_id'] = ObjectId()
            
            # Keep the original UUID as external_id if needed
            if 'id' in agent_data:
                agent_data['external_id'] = agent_data['id']
                del agent_data['id']
            
            result = await self.collection.insert_one(agent_data)
            
            # Return created agent with string ID
            created_agent = await self.collection.find_one({'_id': result.inserted_id})
            return self._serialize_agent(created_agent)
            
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise
        
    async def get(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        result = await self.collection.find_one({"id": agent_id})  # Use string id
        return self._serialize_agent(result) if result else None
        
    async def list_agents(self) -> List[Dict[str, Any]]:
        """Get all agents"""
        try:
            agents = await self.collection.find().to_list(length=None)
            return [self._serialize_agent(agent) for agent in agents]
        except Exception as e:
            logger.error(f"Error listing agents: {str(e)}")
            raise
        
    async def find_by_name_and_type(self, name: str, type: str) -> Optional[Dict[str, Any]]:
        """Find agent by name and type"""
        try:
            agent = await self.collection.find_one({
                'name': name,
                'type': type
            })
            return self._serialize_agent(agent)
        except Exception as e:
            logger.error(f"Error finding agent: {str(e)}")
            raise
        
    async def update(self, agent_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update agent by ID"""
        try:
            result = await self.collection.find_one_and_update(
                {"id": agent_id},  # Use string id
                {"$set": update_data},
                return_document=True
            )
            return self._serialize_agent(result) if result else None
        except Exception as e:
            raise ValueError(f"Failed to update agent: {str(e)}") 
        
    async def update_by_name_type(
        self, 
        name: str, 
        type: str, 
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update agent by name and type"""
        try:
            result = await self.collection.find_one_and_update(
                {"name": name, "type": type},
                {"$set": update_data},
                return_document=True
            )
            return self._serialize_agent(result) if result else None
        except Exception as e:
            raise ValueError(f"Failed to update agent: {str(e)}") 
        
    async def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find agent by name"""
        try:
            agent = await self.collection.find_one({"name": name})
            return self._serialize_agent(agent)
        except Exception as e:
            logger.error(f"Error finding agent: {str(e)}")
            raise 