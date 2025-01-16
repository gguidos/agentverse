from typing import List, Dict, Any, Optional, Set, ClassVar
import logging
from datetime import datetime
from pydantic import Field, ConfigDict

from src.core.agentverse.environment.orders.base import (
    BaseOrder,
    OrderConfig,
    OrderResult
)
from src.core.agentverse.environment.registry import order_registry
from src.core.agentverse.environment.exceptions import ActionError

logger = logging.getLogger(__name__)

class SequentialOrderConfig(OrderConfig):
    """Configuration for sequential order"""
    skip_unavailable: bool = True
    track_skips: bool = True
    allow_reverse: bool = False
    batch_size: int = 1
    min_batch_size: int = 1
    max_skip_retries: int = 3
    
    model_config = ConfigDict(
        extra="allow"
    )

class SequentialMetrics(BaseModel):
    """Metrics for sequential execution"""
    total_turns: int = 0
    skipped_turns: int = 0
    direction_changes: int = 0
    batch_sizes: List[int] = Field(default_factory=list)
    skip_counts: Dict[str, int] = Field(default_factory=dict)

@order_registry.register("sequential")
class SequentialOrder(BaseOrder):
    """Order for sequential turn-taking"""
    
    name: ClassVar[str] = "sequential_order"
    description: ClassVar[str] = "Order for sequential agent execution"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        config: Optional[SequentialOrderConfig] = None
    ):
        super().__init__(config=config or SequentialOrderConfig())
        self.current_index: int = 0
        self.direction: int = 1  # 1 for forward, -1 for reverse
        self.sequential_metrics = SequentialMetrics()
    
    async def _execute(
        self,
        state: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Execute sequential order
        
        Args:
            state: Current environment state
            **kwargs: Additional arguments
            
        Returns:
            Updated state
            
        Raises:
            ActionError: If execution fails
        """
        try:
            # Get next batch of agents
            selected_agents = await self._get_next_batch(state)
            if not selected_agents:
                raise ValueError("No available agents")
            
            # Update state
            new_state = self._update_state_with_selection(
                state=state.copy(),
                selected=selected_agents
            )
            
            # Update metrics
            self._update_sequential_metrics(selected_agents)
            
            return new_state
            
        except Exception as e:
            logger.error(f"Sequential execution failed: {str(e)}")
            raise ActionError(
                message=str(e),
                action=self.name,
                details={
                    "current_index": self.current_index,
                    "direction": self.direction,
                    "state": state
                }
            )
    
    async def _get_next_batch(
        self,
        state: Dict[str, Any]
    ) -> Set[str]:
        """Get next batch of agents
        
        Args:
            state: Current state
            
        Returns:
            Set of selected agent IDs
        """
        selected = set()
        retries = 0
        agents = list(state.get("agents", []))
        
        if not agents:
            return set()
        
        while (
            len(selected) < self.config.batch_size and
            retries < self.config.max_skip_retries
        ):
            # Get next available agent
            next_agent = await self._get_next_available(state)
            if next_agent is None:
                retries += 1
                continue
            
            selected.add(next_agent)
            self._advance_index(len(agents))
        
        # Ensure minimum batch size
        if len(selected) < self.config.min_batch_size:
            remaining = set(agents) - set(state.get("last_agents", []))
            selected.update(
                set(list(remaining)[:self.config.min_batch_size - len(selected)])
            )
        
        return selected
    
    async def _get_next_available(
        self,
        state: Dict[str, Any]
    ) -> Optional[str]:
        """Get next available agent
        
        Args:
            state: Current state
            
        Returns:
            Optional agent ID
        """
        agents = list(state.get("agents", []))
        if not agents:
            return None
            
        start_index = self.current_index
        
        while True:
            # Check if current agent is available
            current_agent = agents[self.current_index]
            if await self._is_agent_available(current_agent, state):
                return current_agent
            
            # Track skip
            if self.config.track_skips:
                self.sequential_metrics.skip_counts[current_agent] = (
                    self.sequential_metrics.skip_counts.get(current_agent, 0) + 1
                )
                self.sequential_metrics.skipped_turns += 1
            
            # Move to next
            self._advance_index(len(agents))
            
            # Check if we've tried all agents
            if self.current_index == start_index:
                if self.config.skip_unavailable:
                    return None
                return agents[start_index]
    
    def _advance_index(self, agent_count: int) -> None:
        """Advance to next index
        
        Args:
            agent_count: Number of agents
        """
        self.current_index = (
            self.current_index + self.direction
        ) % agent_count
    
    async def _is_agent_available(
        self,
        agent_id: str,
        state: Dict[str, Any]
    ) -> bool:
        """Check if agent is available
        
        Args:
            agent_id: Agent to check
            state: Current state
            
        Returns:
            Whether agent is available
        """
        # Check if agent was in last batch
        if agent_id in state.get("last_agents", []):
            return False
        
        # Check agent state
        agent_states = state.get("agent_states", {})
        agent_state = agent_states.get(agent_id, {})
        
        return agent_state.get("status") != "busy"
    
    def _update_state_with_selection(
        self,
        state: Dict[str, Any],
        selected: Set[str]
    ) -> Dict[str, Any]:
        """Update state with selection
        
        Args:
            state: Current state
            selected: Selected agents
            
        Returns:
            Updated state
        """
        state["last_agents"] = list(selected)
        state["last_selection_time"] = datetime.utcnow().isoformat()
        state["selection_history"] = (
            state.get("selection_history", []) + [list(selected)]
        )
        
        return state
    
    def _update_sequential_metrics(
        self,
        selected: Set[str]
    ) -> None:
        """Update sequential metrics
        
        Args:
            selected: Selected agents
        """
        self.sequential_metrics.total_turns += 1
        self.sequential_metrics.batch_sizes.append(len(selected))
    
    def reverse_direction(self) -> None:
        """Reverse the sequence direction"""
        if self.config.allow_reverse:
            self.direction *= -1
            self.sequential_metrics.direction_changes += 1
            logger.info(f"Reversed direction (changes: {self.sequential_metrics.direction_changes})")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics including sequential metrics"""
        metrics = super().get_metrics()
        sequential_metrics = self.sequential_metrics.model_dump()
        
        # Add average metrics
        if self.sequential_metrics.batch_sizes:
            sequential_metrics["avg_batch_size"] = (
                sum(self.sequential_metrics.batch_sizes) /
                len(self.sequential_metrics.batch_sizes)
            )
        
        if self.sequential_metrics.total_turns > 0:
            sequential_metrics["skip_rate"] = (
                self.sequential_metrics.skipped_turns /
                self.sequential_metrics.total_turns
            )
        
        metrics.update(sequential_metrics)
        return metrics
    
    def reset(self) -> None:
        """Reset order state"""
        super().reset()
        self.current_index = 0
        self.direction = 1
        self.sequential_metrics = SequentialMetrics()
        logger.info(f"Reset {self.name} order")

@order_registry.register("sequential_priority")
class PrioritySequentialOrder(SequentialOrder):
    """Sequential order with priority handling"""
    
    name: ClassVar[str] = "priority_sequential_order"
    description: ClassVar[str] = "Sequential order with priority-based selection"
    version: ClassVar[str] = "1.1.0"
    
    class PriorityConfig(SequentialOrderConfig):
        priority_levels: int = 3
        priority_timeout: int = 5  # turns
        priority_boost_threshold: int = 3  # consecutive skips
    
    def __init__(
        self,
        config: Optional[PriorityConfig] = None
    ):
        super().__init__(config=config or self.PriorityConfig())
        self.priorities: Dict[str, int] = {}
        self.priority_timers: Dict[str, int] = {}
    
    async def _is_agent_available(
        self,
        agent_id: str,
        state: Dict[str, Any]
    ) -> bool:
        """Check availability with priority
        
        Args:
            agent_id: Agent to check
            state: Current state
            
        Returns:
            Whether agent is available
        """
        if not await super()._is_agent_available(agent_id, state):
            return False
        
        # Update priority timer
        self.priority_timers[agent_id] = (
            self.priority_timers.get(agent_id, 0) + 1
        )
        
        # Check if timeout reached
        if self.priority_timers[agent_id] >= self.config.priority_timeout:
            return True
        
        # Check consecutive skips
        skip_count = self.sequential_metrics.skip_counts.get(agent_id, 0)
        if skip_count >= self.config.priority_boost_threshold:
            return True
        
        # Check priority
        return self.priorities.get(agent_id, 0) >= self._get_min_priority()
    
    def _get_min_priority(self) -> int:
        """Get minimum priority for current turn
        
        Returns:
            Minimum required priority
        """
        turn = self.sequential_metrics.total_turns
        return max(
            0,
            self.config.priority_levels - 1 - (turn % self.config.priority_levels)
        )
    
    def set_priority(
        self,
        agent_id: str,
        priority: int
    ) -> None:
        """Set agent priority
        
        Args:
            agent_id: Agent ID
            priority: Priority level
        """
        self.priorities[agent_id] = max(
            0,
            min(priority, self.config.priority_levels - 1)
        )
        logger.debug(f"Set priority {priority} for agent {agent_id}")
    
    def reset(self) -> None:
        """Reset order state"""
        super().reset()
        self.priorities.clear()
        self.priority_timers.clear() 