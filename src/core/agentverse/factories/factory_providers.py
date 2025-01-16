from typing import Dict, Any, Optional, Type
import logging

from src.core.agentverse.factories.agent_factory import AgentFactory, AgentConfig
from src.core.agentverse.tools.base import BaseTool
from src.core.agentverse.memory.base import BaseMemory
from src.core.agentverse.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

def create_agent_factory(
    embeddings_client: Any,
    openai_service: Any,
    message_bus: Any,
    chroma_db: Any,
    available_tools: Optional[Dict[str, BaseTool]] = None,
    default_memory_class: Optional[Type[BaseMemory]] = None,
    default_config: Optional[AgentConfig] = None
) -> AgentFactory:
    """Create and configure agent factory
    
    Args:
        embeddings_client: Client for embeddings
        openai_service: OpenAI service instance
        message_bus: Message bus instance
        chroma_db: ChromaDB instance
        available_tools: Optional tool dictionary
        default_memory_class: Optional default memory class
        default_config: Optional default agent configuration
        
    Returns:
        Configured agent factory
        
    Raises:
        ConfigurationError: If factory creation fails
    """
    try:
        # Initialize services
        llm_service = _init_llm_service(
            openai_service=openai_service,
            embeddings_client=embeddings_client
        )
        
        memory_service = _init_memory_service(
            chroma_db=chroma_db,
            message_bus=message_bus,
            default_memory_class=default_memory_class
        )
        
        parser_service = _init_parser_service()
        
        # Create factory
        factory = AgentFactory(
            llm_service=llm_service,
            memory_service=memory_service,
            parser_service=parser_service,
            available_tools=available_tools or {},
            default_memory_class=default_memory_class
        )
        
        # Apply default configuration if provided
        if default_config:
            factory.default_config = default_config
        
        logger.info(
            f"Created agent factory with "
            f"{len(available_tools or {})} tools available"
        )
        return factory
        
    except Exception as e:
        logger.error(f"Failed to create agent factory: {str(e)}")
        raise ConfigurationError(
            message=f"Agent factory creation failed: {str(e)}",
            details={
                "tools": len(available_tools or {}),
                "memory_class": default_memory_class.__name__ if default_memory_class else None
            }
        )

def _init_llm_service(
    openai_service: Any,
    embeddings_client: Any
) -> Any:
    """Initialize LLM service
    
    Args:
        openai_service: OpenAI service instance
        embeddings_client: Embeddings client
        
    Returns:
        Configured LLM service
    """
    # Configure LLM service
    llm_service = openai_service
    llm_service.embeddings_client = embeddings_client
    return llm_service

def _init_memory_service(
    chroma_db: Any,
    message_bus: Any,
    default_memory_class: Optional[Type[BaseMemory]] = None
) -> Any:
    """Initialize memory service
    
    Args:
        chroma_db: ChromaDB instance
        message_bus: Message bus instance
        default_memory_class: Optional default memory class
        
    Returns:
        Configured memory service
    """
    # Configure memory service
    memory_service = {
        "chroma_db": chroma_db,
        "message_bus": message_bus,
        "default_class": default_memory_class
    }
    return memory_service

def _init_parser_service() -> Any:
    """Initialize parser service
    
    Returns:
        Configured parser service
    """
    # Configure parser service
    # TODO: Implement proper parser service
    return {} 