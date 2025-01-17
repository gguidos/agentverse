"""Agent Factory Module"""

from typing import Dict, Any, Optional
from pydantic import Field

from src.core.agentverse.factories.base import BaseFactory, FactoryConfig
from src.core.agentverse.entities.agent import Agent, AgentConfig
from src.core.agentverse.llm import get_llm
from src.core.agentverse.testing.mocks.llm import MockLLM
from src.core.agentverse.agents.assistant import AssistantAgent

class AgentFactoryConfig(FactoryConfig):
    """Agent factory configuration"""
    id: Optional[str] = None
    capabilities: Optional[list] = Field(default_factory=list)
    max_tasks: int = 5
    memory_limit: float = 100.0
    llm: Dict[str, Any] = Field(default_factory=dict)

class AgentFactory(BaseFactory[Agent]):
    """Factory for creating agents"""
    
    # Register agent types with actual classes
    AGENT_TYPES = {
        "assistant": AssistantAgent,
        # Add other agent types here
    }
    
    @classmethod
    async def create(
        cls,
        config: AgentFactoryConfig,
        **kwargs
    ) -> Agent:
        """Create an agent instance"""
        if not await cls.validate_config(config):
            raise ValueError("Invalid agent configuration")
            
        # Configure LLM
        llm_config = config.llm
        llm_type = llm_config.get("type")
        
        # Use mock LLM for testing
        if llm_type == "mock":
            llm = MockLLM(**llm_config)
        else:
            llm = get_llm(llm_type, **llm_config)
            
        # Create agent config
        agent_config = AgentConfig(
            id=config.id,
            type=config.type,
            name=config.name,
            capabilities=config.capabilities,
            max_tasks=config.max_tasks,
            memory_limit=config.memory_limit,
            metadata=config.metadata,
            llm=llm
        )
        
        # Get agent class
        if config.type not in cls.AGENT_TYPES:
            raise ValueError(f"Unknown agent type: {config.type}")
            
        agent_class = cls.AGENT_TYPES[config.type]
        
        # Create agent
        return agent_class(
            config=agent_config,
            llm=llm  # Pass LLM instance directly
        )
    
    @classmethod
    async def validate_config(
        cls,
        config: AgentFactoryConfig
    ) -> bool:
        """Validate agent factory configuration"""
        if config.max_tasks < 1:
            return False
        if config.memory_limit <= 0:
            return False
        if config.type not in cls.AGENT_TYPES:
            return False
        return True
    
    @classmethod 
    def get_defaults(cls) -> Dict[str, Any]:
        """Get default agent configuration"""
        return {
            "type": "assistant",
            "capabilities": [],
            "max_tasks": 5,
            "memory_limit": 100.0,
            "llm": {
                "type": "mock"
            }
        } 