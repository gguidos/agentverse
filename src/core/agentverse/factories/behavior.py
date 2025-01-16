"""Behavior Factory Module"""

from typing import Dict, Any, Optional, List
from pydantic import Field

from src.core.agentverse.factories.base import BaseFactory, FactoryConfig

class BehaviorFactoryConfig(FactoryConfig):
    """Behavior factory configuration"""
    behavior_type: str = "reactive"  # reactive, proactive, cognitive, emotional
    triggers: List[Dict[str, Any]] = Field(default_factory=list)
    responses: List[Dict[str, Any]] = Field(default_factory=list)
    state: Dict[str, Any] = Field(default_factory=dict)
    learning_rate: float = 0.1

class BehaviorFactory(BaseFactory):
    """Factory for creating agent behaviors"""
    
    @classmethod
    async def create(
        cls,
        config: BehaviorFactoryConfig,
        **kwargs
    ) -> Any:
        """Create a behavior instance"""
        if not await cls.validate_config(config):
            raise ValueError("Invalid behavior configuration")
            
        # Create appropriate behavior type
        if config.behavior_type == "reactive":
            return await cls._create_reactive_behavior(config, **kwargs)
        elif config.behavior_type == "proactive":
            return await cls._create_proactive_behavior(config, **kwargs)
        elif config.behavior_type == "cognitive":
            return await cls._create_cognitive_behavior(config, **kwargs)
        elif config.behavior_type == "emotional":
            return await cls._create_emotional_behavior(config, **kwargs)
        else:
            raise ValueError(f"Unsupported behavior type: {config.behavior_type}")
    
    @classmethod
    async def validate_config(
        cls,
        config: BehaviorFactoryConfig
    ) -> bool:
        """Validate behavior factory configuration"""
        valid_types = ["reactive", "proactive", "cognitive", "emotional"]
        if config.behavior_type not in valid_types:
            return False
        if not config.triggers and not config.responses:
            return False
        if config.learning_rate < 0 or config.learning_rate > 1:
            return False
        return True
    
    @classmethod
    def get_defaults(cls) -> Dict[str, Any]:
        """Get default behavior configuration"""
        return {
            "type": "behavior",
            "behavior_type": "reactive",
            "triggers": [],
            "responses": [],
            "state": {},
            "learning_rate": 0.1
        }
    
    @classmethod
    async def _create_reactive_behavior(cls, config: BehaviorFactoryConfig, **kwargs):
        """Create reactive behavior"""
        # Implementation for reactive behavior
        pass
    
    @classmethod
    async def _create_proactive_behavior(cls, config: BehaviorFactoryConfig, **kwargs):
        """Create proactive behavior"""
        # Implementation for proactive behavior
        pass
    
    @classmethod
    async def _create_cognitive_behavior(cls, config: BehaviorFactoryConfig, **kwargs):
        """Create cognitive behavior"""
        # Implementation for cognitive behavior
        pass
    
    @classmethod
    async def _create_emotional_behavior(cls, config: BehaviorFactoryConfig, **kwargs):
        """Create emotional behavior"""
        # Implementation for emotional behavior
        pass 