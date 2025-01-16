from typing import Dict, Any, List, Optional, ClassVar, Type
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging

from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.tools.base import BaseTool
from src.core.agentverse.memory.base import BaseMemory
from src.core.agentverse.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

class AgentConfig(BaseModel):
    """Configuration for agent creation"""
    name: str
    capabilities: List[str] = Field(default_factory=list)
    prompt_template: str = "You are a helpful AI assistant."
    memory_config: Optional[Dict[str, Any]] = None
    tool_config: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        extra="allow"
    )

class AgentMetrics(BaseModel):
    """Metrics for agent factory"""
    total_created: int = 0
    unique_agents: int = 0
    creation_errors: int = 0
    last_creation: Optional[datetime] = None
    creation_times: List[float] = Field(default_factory=list)
    capability_usage: Dict[str, int] = Field(default_factory=dict)

class AgentFactory:
    """Factory for creating and managing agents"""
    
    name: ClassVar[str] = "agent_factory"
    description: ClassVar[str] = "Factory for creating and managing agents"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        llm_service: Any,
        memory_service: Any,
        parser_service: Any,
        available_tools: Dict[str, BaseTool],
        default_memory_class: Optional[Type[BaseMemory]] = None
    ):
        self.llm_service = llm_service
        self.memory_service = memory_service
        self.parser_service = parser_service
        self.available_tools = available_tools
        self.default_memory_class = default_memory_class
        self._agents: Dict[str, BaseAgent] = {}
        self.metrics = AgentMetrics()
        logger.info(f"Initialized {self.name} v{self.version}")
    
    async def get_agent(
        self,
        agent_id: str,
        config: Optional[AgentConfig] = None
    ) -> BaseAgent:
        """Create or retrieve an agent
        
        Args:
            agent_id: Unique agent identifier
            config: Optional agent configuration
            
        Returns:
            Agent instance
            
        Raises:
            ConfigurationError: If agent creation fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Return existing agent if available
            if agent_id in self._agents:
                return self._agents[agent_id]
            
            # Create new agent
            config = config or AgentConfig(name=f"agent_{agent_id}")
            
            # Select tools based on capabilities
            selected_tools = self._select_tools(config.capabilities)
            
            # Create memory instance
            memory = self._create_memory(
                agent_id=agent_id,
                config=config.memory_config
            )
            
            # Create agent
            agent = BaseAgent(
                name=config.name,
                llm=self.llm_service,
                memory=memory,
                parser=self.parser_service,
                prompt_template=config.prompt_template,
                tools=selected_tools,
                metadata={
                    "id": agent_id,
                    "capabilities": config.capabilities,
                    **config.metadata
                }
            )
            
            # Store agent
            self._agents[agent_id] = agent
            
            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(
                agent_id=agent_id,
                capabilities=config.capabilities,
                duration=duration
            )
            
            return agent
            
        except Exception as e:
            self.metrics.creation_errors += 1
            logger.error(f"Agent creation failed: {str(e)}")
            raise ConfigurationError(
                message=str(e),
                config_key=agent_id,
                details={
                    "capabilities": config.capabilities if config else None,
                    "duration": (datetime.utcnow() - start_time).total_seconds()
                }
            )
    
    def _select_tools(
        self,
        capabilities: List[str]
    ) -> Dict[str, BaseTool]:
        """Select tools based on capabilities
        
        Args:
            capabilities: Required capabilities
            
        Returns:
            Selected tools
        """
        if not capabilities:
            return {}
            
        selected_tools = {}
        for capability in capabilities:
            if capability in self.available_tools:
                selected_tools[capability] = self.available_tools[capability]
                self.metrics.capability_usage[capability] = (
                    self.metrics.capability_usage.get(capability, 0) + 1
                )
            else:
                logger.warning(f"Capability not available: {capability}")
                
        return selected_tools
    
    def _create_memory(
        self,
        agent_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseMemory:
        """Create memory instance for agent
        
        Args:
            agent_id: Agent identifier
            config: Optional memory configuration
            
        Returns:
            Memory instance
            
        Raises:
            ConfigurationError: If memory creation fails
        """
        try:
            if self.memory_service:
                return self.memory_service.create_memory(
                    agent_id=agent_id,
                    config=config
                )
            
            if self.default_memory_class:
                return self.default_memory_class(
                    agent_id=agent_id,
                    **(config or {})
                )
            
            raise ValueError("No memory service or default class configured")
            
        except Exception as e:
            raise ConfigurationError(
                message=f"Memory creation failed: {str(e)}",
                config_key=agent_id,
                details={"config": config}
            )
    
    def _update_metrics(
        self,
        agent_id: str,
        capabilities: List[str],
        duration: float
    ) -> None:
        """Update factory metrics
        
        Args:
            agent_id: Created agent ID
            capabilities: Agent capabilities
            duration: Creation duration
        """
        self.metrics.total_created += 1
        if agent_id not in self._agents:
            self.metrics.unique_agents += 1
        
        self.metrics.last_creation = datetime.utcnow()
        self.metrics.creation_times.append(duration)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get factory metrics
        
        Returns:
            Factory metrics
        """
        metrics = self.metrics.model_dump()
        
        # Add average creation time
        if self.metrics.creation_times:
            metrics["avg_creation_time"] = (
                sum(self.metrics.creation_times) /
                len(self.metrics.creation_times)
            )
        
        # Add capability distribution
        total_capabilities = sum(self.metrics.capability_usage.values())
        if total_capabilities > 0:
            metrics["capability_distribution"] = {
                cap: count / total_capabilities
                for cap, count in self.metrics.capability_usage.items()
            }
        
        return metrics
    
    def reset(self) -> None:
        """Reset factory state"""
        self._agents.clear()
        self.metrics = AgentMetrics()
        logger.info(f"Reset {self.name}") 