from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, ClassVar, Set
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging

from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.environment.registry import describer_registry
from src.core.agentverse.environment.exceptions import EnvironmentError

logger = logging.getLogger(__name__)

class DescriberConfig(BaseModel):
    """Configuration for environment describers"""
    include_history: bool = True
    max_history_length: int = 5
    include_metrics: bool = True
    include_agent_states: bool = True
    include_timestamps: bool = True
    format_type: str = "text"
    max_description_length: int = 1000

class EnvironmentContext(BaseModel):
    """Structured environment context"""
    description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    turn: int
    agent_count: int
    active_agents: Set[str] = Field(default_factory=set)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

class DescriberMetrics(BaseModel):
    """Metrics for describer execution"""
    descriptions_generated: int = 0
    total_tokens: int = 0
    errors: int = 0
    last_execution: Optional[datetime] = None
    execution_times: List[float] = Field(default_factory=list)

class BaseDescriber(ABC):
    """Base class for environment describers"""
    
    name: ClassVar[str] = "base_describer"
    description: ClassVar[str] = "Base describer implementation"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(self, config: Optional[DescriberConfig] = None):
        self.config = config or DescriberConfig()
        self.metrics = DescriberMetrics()
        logger.info(f"Initialized {self.name} describer v{self.version}")
    
    async def get_description(
        self,
        environment: BaseEnvironment,
        agent_id: Optional[str] = None,
        **kwargs
    ) -> List[EnvironmentContext]:
        """Get environment description for agents
        
        Args:
            environment: Environment to describe
            agent_id: Optional agent ID to filter for
            **kwargs: Additional arguments
            
        Returns:
            List of environment contexts
            
        Raises:
            EnvironmentError: If description generation fails
        """
        start_time = datetime.utcnow()
        try:
            # Generate base descriptions
            descriptions = await self._generate_descriptions(
                environment=environment,
                agent_id=agent_id,
                **kwargs
            )
            
            # Add additional context based on configuration
            if self.config.include_history:
                descriptions = await self._add_history_context(
                    environment=environment,
                    descriptions=descriptions
                )
                
            if self.config.include_metrics:
                descriptions = await self._add_metrics_context(
                    environment=environment,
                    descriptions=descriptions
                )
                
            if self.config.include_agent_states:
                descriptions = await self._add_agent_context(
                    environment=environment,
                    descriptions=descriptions
                )
            
            # Validate and format descriptions
            descriptions = self._validate_descriptions(descriptions)
            
            # Update metrics
            self.metrics.descriptions_generated += len(descriptions)
            self.metrics.total_tokens += sum(
                len(desc.description.split()) for desc in descriptions
            )
            
            return descriptions
            
        except Exception as e:
            self.metrics.errors += 1
            logger.error(f"Failed to generate description: {str(e)}")
            raise EnvironmentError(f"Description generation failed: {str(e)}")
            
        finally:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.execution_times.append(duration)
            self.metrics.last_execution = datetime.utcnow()
    
    @abstractmethod
    async def _generate_descriptions(
        self,
        environment: BaseEnvironment,
        agent_id: Optional[str] = None,
        **kwargs
    ) -> List[EnvironmentContext]:
        """Generate base descriptions
        
        Args:
            environment: Environment to describe
            agent_id: Optional agent ID to filter for
            **kwargs: Additional arguments
            
        Returns:
            List of environment contexts
        """
        pass
    
    async def _add_history_context(
        self,
        environment: BaseEnvironment,
        descriptions: List[EnvironmentContext]
    ) -> List[EnvironmentContext]:
        """Add conversation history context
        
        Args:
            environment: Environment instance
            descriptions: Current descriptions
            
        Returns:
            Updated descriptions
        """
        history = environment.state.messages[-self.config.max_history_length:]
        
        for desc in descriptions:
            desc.metadata["history"] = [
                {
                    "sender": msg.get("sender"),
                    "content": msg.get("content"),
                    "turn": msg.get("turn", i),
                    "timestamp": msg.get("timestamp")
                }
                for i, msg in enumerate(history)
            ]
        
        return descriptions
    
    async def _add_metrics_context(
        self,
        environment: BaseEnvironment,
        descriptions: List[EnvironmentContext]
    ) -> List[EnvironmentContext]:
        """Add metrics context
        
        Args:
            environment: Environment instance
            descriptions: Current descriptions
            
        Returns:
            Updated descriptions
        """
        metrics = environment.state.metrics
        
        for desc in descriptions:
            desc.metadata["metrics"] = {
                "messages": metrics.get("total_messages", 0),
                "turns": environment.state.current_turn,
                "agents": len(environment.state.agents),
                "performance": {
                    k: v for k, v in metrics.items()
                    if isinstance(v, (int, float))
                }
            }
        
        return descriptions
    
    async def _add_agent_context(
        self,
        environment: BaseEnvironment,
        descriptions: List[EnvironmentContext]
    ) -> List[EnvironmentContext]:
        """Add agent state context
        
        Args:
            environment: Environment instance
            descriptions: Current descriptions
            
        Returns:
            Updated descriptions
        """
        for desc in descriptions:
            agent_id = desc.metadata.get("agent_id")
            if agent_id and agent_id in environment.state.agent_states:
                desc.metadata["agent_state"] = environment.state.agent_states[agent_id]
        
        return descriptions
    
    def _validate_descriptions(
        self,
        descriptions: List[EnvironmentContext]
    ) -> List[EnvironmentContext]:
        """Validate and format descriptions
        
        Args:
            descriptions: Descriptions to validate
            
        Returns:
            Validated descriptions
        """
        validated = []
        
        for desc in descriptions:
            # Truncate if needed
            if len(desc.description) > self.config.max_description_length:
                desc.description = (
                    desc.description[:self.config.max_description_length] + "..."
                )
            
            # Format based on configuration
            if self.config.format_type == "markdown":
                desc.description = f"```markdown\n{desc.description}\n```"
            elif self.config.format_type == "json":
                import json
                desc.description = json.dumps({
                    "description": desc.description,
                    "metadata": desc.metadata
                })
            
            validated.append(desc)
        
        return validated
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get describer metrics"""
        metrics = self.metrics.model_dump()
        if self.metrics.execution_times:
            metrics["avg_execution_time"] = (
                sum(self.metrics.execution_times) /
                len(self.metrics.execution_times)
            )
        return metrics
    
    def reset(self) -> None:
        """Reset describer state"""
        self.metrics = DescriberMetrics()
        logger.info(f"Reset {self.name} describer")
    
    def __str__(self) -> str:
        return f"{self.name}Describer(v{self.version})"
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"config={self.config.model_dump()}, "
            f"descriptions={self.metrics.descriptions_generated})"
        )

@describer_registry.register("basic")
class BasicDescriber(BaseDescriber):
    """Basic environment describer"""
    
    name: ClassVar[str] = "basic_describer"
    description: ClassVar[str] = "Basic environment state describer"
    version: ClassVar[str] = "1.1.0"
    
    async def _generate_descriptions(
        self,
        environment: BaseEnvironment,
        agent_id: Optional[str] = None,
        **kwargs
    ) -> List[EnvironmentContext]:
        """Generate basic descriptions
        
        Args:
            environment: Environment to describe
            agent_id: Optional agent ID to filter for
            **kwargs: Additional arguments
            
        Returns:
            List of environment contexts
        """
        descriptions = []
        
        for i, agent_id in enumerate(environment.state.agents):
            if agent_id is not None and agent_id != agent_id:
                continue
            
            context = EnvironmentContext(
                description=(
                    f"Turn {environment.state.current_turn}"
                    f"{f'/{environment.state.max_turns}' if environment.state.max_turns else ''}"
                    f" with {len(environment.state.agents)} agents."
                    f"\nActive agent: {environment.state.active_agent or 'None'}"
                    f"\nStatus: {environment.state.status}"
                ),
                turn=environment.state.current_turn,
                agent_count=len(environment.state.agents),
                active_agents={environment.state.active_agent} if environment.state.active_agent else set(),
                metadata={
                    "agent_id": agent_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            descriptions.append(context)
        
        return descriptions 