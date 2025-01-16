from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import datetime
from typing import Optional, Dict, Any, ClassVar
import logging
import uuid

logger = logging.getLogger(__name__)

class EntityMetadata(BaseModel):
    """Metadata for entities"""
    version: str = "1.0.0"
    source: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    custom_data: Dict[str, Any] = Field(default_factory=dict)

class BaseEntity(BaseModel):
    """Base entity with common fields and functionality"""
    
    # Entity identification
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    description: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    
    # Status and metadata
    is_active: bool = True
    is_deleted: bool = False
    metadata: EntityMetadata = Field(default_factory=EntityMetadata)
    
    # Class configuration
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    # Class variables
    entity_type: ClassVar[str] = "base"
    entity_version: ClassVar[str] = "1.0.0"
    
    @model_validator(mode='before')
    @classmethod
    def update_timestamps(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Update timestamps on entity modification"""
        now = datetime.utcnow()
        
        if "created_at" not in values:
            values["created_at"] = now
            
        values["updated_at"] = now
        
        return values
    
    def mark_deleted(self) -> None:
        """Mark entity as deleted"""
        self.is_deleted = True
        self.is_active = False
        self.deleted_at = datetime.utcnow()
        logger.info(f"Entity {self.id} marked as deleted")
    
    def restore(self) -> None:
        """Restore deleted entity"""
        self.is_deleted = False
        self.is_active = True
        self.deleted_at = None
        logger.info(f"Entity {self.id} restored")
    
    def update_metadata(self, **kwargs) -> None:
        """Update entity metadata
        
        Args:
            **kwargs: Key-value pairs to update in metadata
        """
        for key, value in kwargs.items():
            if key == "tags":
                self.metadata.tags.update(value)
            elif key == "custom_data":
                self.metadata.custom_data.update(value)
            else:
                setattr(self.metadata, key, value)
        
        logger.debug(f"Updated metadata for entity {self.id}")
    
    def to_dict(self, exclude_none: bool = True) -> Dict[str, Any]:
        """Convert entity to dictionary
        
        Args:
            exclude_none: Whether to exclude None values
            
        Returns:
            Dict representation of entity
        """
        return self.model_dump(
            exclude_none=exclude_none,
            exclude_defaults=False
        )
    
    def clone(self, **kwargs) -> 'BaseEntity':
        """Create a clone of this entity
        
        Args:
            **kwargs: Fields to override in the clone
            
        Returns:
            New entity instance
        """
        data = self.to_dict()
        # Remove unique fields
        data.pop('id', None)
        data.pop('created_at', None)
        data.pop('updated_at', None)
        data.pop('deleted_at', None)
        
        # Override with provided values
        data.update(kwargs)
        
        return self.__class__(**data)
    
    @property
    def age(self) -> float:
        """Get entity age in seconds"""
        return (datetime.utcnow() - self.created_at).total_seconds()
    
    @property
    def is_new(self) -> bool:
        """Check if entity is newly created (less than 1 hour old)"""
        return self.age < 3600
    
    def __str__(self) -> str:
        """String representation of entity"""
        return f"{self.entity_type}(id={self.id}, name={self.name})"
    
    def __repr__(self) -> str:
        """Detailed string representation of entity"""
        return (
            f"{self.__class__.__name__}("
            f"id={self.id}, "
            f"name={self.name}, "
            f"created={self.created_at.isoformat()}, "
            f"active={self.is_active})"
        ) 