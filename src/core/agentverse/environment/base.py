from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, ClassVar, Set
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging

from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.message.base import Message
from src.core.agentverse.environment.exceptions import (
    ActionError,
    StateError,
    RuleValidationError
)

logger = logging.getLogger(__name__)

class EnvironmentState(BaseModel):
    """State of the environment"""
    current_turn: int = 0
    max_turns: Optional[int] = None
    status: str = "initialized"
    agents: List[str] = Field(default_factory=list)
    active_agent: Optional[str] = None
    agent_states: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    message_history: List[Message] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

class EnvironmentMetrics(BaseModel):
    """Metrics for environment execution"""
    total_turns: int = 0
    total_messages: int = 0
    total_actions: int = 0
    failed_actions: int = 0
    last_action: Optional[datetime] = None
    execution_times: List[float] = Field(default_factory=list)
    agent_stats: Dict[str, Dict[str, int]] = Field(default_factory=dict)

class BaseEnvironment(ABC):
    """Base class for environments"""
    
    name: ClassVar[str] = "base_environment"
    description: ClassVar[str] = "Base environment implementation"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        agents: List[BaseAgent],
        max_turns: Optional[int] = None,
        **kwargs
    ):
        self.agents = agents
        self.state = EnvironmentState(
            max_turns=max_turns,
            agents=[agent.name for agent in agents]
        )
        self.metrics = EnvironmentMetrics()
        self._validate_agents()
        logger.info(f"Initialized {self.name} environment v{self.version}")
    
    def _validate_agents(self) -> None:
        """Validate agent configuration
        
        Raises:
            StateError: If agent configuration is invalid
        """
        # Check for duplicate agent names
        names = [agent.name for agent in self.agents]
        if len(names) != len(set(names)):
            raise StateError(
                message="Duplicate agent names found",
                details={"names": names}
            )
        
        # Initialize agent states
        for agent in self.agents:
            self.state.agent_states[agent.name] = {
                "status": "ready",
                "last_action": None,
                "action_count": 0
            }
    
    @abstractmethod
    async def step(self) -> None:
        """Execute one environment step"""
        pass
    
    async def run(self, max_turns: Optional[int] = None) -> None:
        """Run environment for specified turns
        
        Args:
            max_turns: Maximum turns to run
            
        Raises:
            StateError: If run fails
        """
        if max_turns is not None:
            self.state.max_turns = max_turns
        
        try:
            while not self._is_done():
                await self.step()
                self.state.current_turn += 1
                
        except Exception as e:
            self.state.status = "error"
            logger.error(f"Environment run failed: {str(e)}")
            raise StateError(
                message=str(e),
                details={
                    "turn": self.state.current_turn,
                    "status": self.state.status
                }
            )
    
    def _is_done(self) -> bool:
        """Check if environment is done
        
        Returns:
            Whether environment is done
        """
        if self.state.status == "error":
            return True
            
        if self.state.max_turns is not None:
            return self.state.current_turn >= self.state.max_turns
            
        return False
    
    async def add_message(self, message: Message) -> None:
        """Add message to history
        
        Args:
            message: Message to add
        """
        self.state.message_history.append(message)
        self.metrics.total_messages += 1
        
        # Update agent stats
        if message.sender:
            stats = self.metrics.agent_stats.setdefault(
                message.sender,
                {"messages": 0, "actions": 0}
            )
            stats["messages"] += 1
    
    async def update_agent_state(
        self,
        agent_name: str,
        updates: Dict[str, Any]
    ) -> None:
        """Update agent state
        
        Args:
            agent_name: Agent to update
            updates: State updates
            
        Raises:
            StateError: If agent not found
        """
        if agent_name not in self.state.agent_states:
            raise StateError(
                message=f"Agent {agent_name} not found",
                details={"available": list(self.state.agent_states.keys())}
            )
        
        self.state.agent_states[agent_name].update(updates)
    
    def get_agent_by_name(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name
        
        Args:
            name: Agent name
            
        Returns:
            Optional agent instance
        """
        for agent in self.agents:
            if agent.name == name:
                return agent
        return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get environment metrics
        
        Returns:
            Environment metrics
        """
        metrics = self.metrics.model_dump()
        
        # Add average metrics
        if self.metrics.execution_times:
            metrics["avg_execution_time"] = (
                sum(self.metrics.execution_times) /
                len(self.metrics.execution_times)
            )
        
        # Add success rate
        if self.metrics.total_actions > 0:
            metrics["action_success_rate"] = (
                (self.metrics.total_actions - self.metrics.failed_actions) /
                self.metrics.total_actions
            )
        
        return metrics
    
    def reset(self) -> None:
        """Reset environment state"""
        self.state = EnvironmentState(
            max_turns=self.state.max_turns,
            agents=[agent.name for agent in self.agents]
        )
        self.metrics = EnvironmentMetrics()
        self._validate_agents()
        logger.info(f"Reset {self.name} environment")
    
    def __str__(self) -> str:
        return f"{self.name}Environment(v{self.version})"
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"agents={len(self.agents)}, "
            f"turn={self.state.current_turn})"
        ) 