"""Entity Registry Module"""

from typing import Dict, Any, Optional, Type
import logging

from src.core.agentverse.entities.base import BaseEntity

logger = logging.getLogger(__name__)

class EntityRegistry:
    """Registry for managing entities"""
    
    def __init__(self):
        self.entities: Dict[str, BaseEntity] = {}
        self.types: Dict[str, Dict[str, BaseEntity]] = {}
    
    def register(self, entity: BaseEntity) -> None:
        """Register an entity
        
        Args:
            entity: Entity to register
        """
        self.entities[entity.id] = entity
        
        if entity.type not in self.types:
            self.types[entity.type] = {}
        self.types[entity.type][entity.id] = entity
        
        logger.info(f"Registered entity: {entity.id} ({entity.type})")
    
    def get(self, entity_id: str) -> Optional[BaseEntity]:
        """Get entity by ID
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Entity if found, None otherwise
        """
        return self.entities.get(entity_id)
    
    def get_by_type(self, entity_type: str) -> Dict[str, BaseEntity]:
        """Get all entities of specified type
        
        Args:
            entity_type: Entity type
            
        Returns:
            Dictionary of entities
        """
        return self.types.get(entity_type, {})
    
    def unregister(self, entity_id: str) -> None:
        """Unregister an entity
        
        Args:
            entity_id: Entity identifier
        """
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            del self.entities[entity_id]
            del self.types[entity.type][entity_id]
            logger.info(f"Unregistered entity: {entity_id}") 