"""Personality Factory Module"""

from typing import Dict, Any, Optional, List
from pydantic import Field

from src.core.agentverse.factories.base import BaseFactory, FactoryConfig

class PersonalityFactoryConfig(FactoryConfig):
    """Personality factory configuration"""
    personality_type: str = "basic"  # basic, dynamic, adaptive, composite
    traits: Dict[str, float] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    memory: Dict[str, Any] = Field(default_factory=dict)
    adaptation_rate: float = 0.05

class PersonalityFactory(BaseFactory):
    """Factory for creating agent personalities"""
    
    @classmethod
    async def create(
        cls,
        config: PersonalityFactoryConfig,
        **kwargs
    ) -> Any:
        """Create a personality instance"""
        if not await cls.validate_config(config):
            raise ValueError("Invalid personality configuration")
            
        # Create appropriate personality type
        if config.personality_type == "basic":
            return await cls._create_basic_personality(config, **kwargs)
        elif config.personality_type == "dynamic":
            return await cls._create_dynamic_personality(config, **kwargs)
        elif config.personality_type == "adaptive":
            return await cls._create_adaptive_personality(config, **kwargs)
        elif config.personality_type == "composite":
            return await cls._create_composite_personality(config, **kwargs)
        else:
            raise ValueError(f"Unsupported personality type: {config.personality_type}")
    
    @classmethod
    async def validate_config(
        cls,
        config: PersonalityFactoryConfig
    ) -> bool:
        """Validate personality factory configuration"""
        valid_types = ["basic", "dynamic", "adaptive", "composite"]
        if config.personality_type not in valid_types:
            return False
        if not config.traits:
            return False
        if config.adaptation_rate < 0 or config.adaptation_rate > 1:
            return False
        return True
    
    @classmethod
    def get_defaults(cls) -> Dict[str, Any]:
        """Get default personality configuration"""
        return {
            "type": "personality",
            "personality_type": "basic",
            "traits": {
                "openness": 0.5,
                "conscientiousness": 0.5,
                "extraversion": 0.5,
                "agreeableness": 0.5,
                "neuroticism": 0.5
            },
            "preferences": {},
            "memory": {},
            "adaptation_rate": 0.05
        }
    
    @classmethod
    async def _create_basic_personality(cls, config: PersonalityFactoryConfig, **kwargs):
        """Create basic personality"""
        # Implementation for basic personality
        pass
    
    @classmethod
    async def _create_dynamic_personality(cls, config: PersonalityFactoryConfig, **kwargs):
        """Create dynamic personality"""
        # Implementation for dynamic personality
        pass
    
    @classmethod
    async def _create_adaptive_personality(cls, config: PersonalityFactoryConfig, **kwargs):
        """Create adaptive personality"""
        # Implementation for adaptive personality
        pass
    
    @classmethod
    async def _create_composite_personality(cls, config: PersonalityFactoryConfig, **kwargs):
        """Create composite personality"""
        # Implementation for composite personality
        pass 