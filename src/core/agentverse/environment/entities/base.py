"""Base Entity Module"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class EntityState(BaseModel):
    """Entity state model"""
    status: str = "created"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EntityConfig(BaseModel):
    """Entity configuration"""
    id: str
    type: str
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseEntity(ABC):
    """Base class for all entities"""
    
    def __init__(self, config: EntityConfig):
        self.config = config
        self.state = EntityState()
    
    @property
    def id(self) -> str:
        """Get entity ID"""
        return self.config.id
    
    @property
    def type(self) -> str:
        """Get entity type"""
        return self.config.type
    
    @abstractmethod
    async def update(self, updates: Dict[str, Any]) -> None:
        """Update entity state
        
        Args:
            updates: State updates to apply
        """
        self.state.modified_at = datetime.utcnow()
        self.state.metadata.update(updates)
    
    @abstractmethod
    async def validate(self) -> bool:
        """Validate entity state"""
        return True 