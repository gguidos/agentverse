from typing import List, Dict, Any, Optional, Set, ClassVar
import logging
import asyncio
from datetime import datetime
from pydantic import Field, ConfigDict

from src.core.agentverse.environment.orders.base import BaseOrder, OrderConfig, OrderResult
from src.core.agentverse.environment.registry import order_registry
from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.environment.exceptions import ActionError

logger = logging.getLogger(__name__)

class ConcurrentOrderConfig(OrderConfig):
    """Configuration for concurrent orders"""
    max_concurrent: int = 0  # 0 means no limit
    enforce_dependencies: bool = False
    track_timing: bool = True
    timeout_per_agent: float = 10.0
    max_batch_retries: int = 2
    
    model_config = ConfigDict(
        extra="allow"
    )

class ConcurrentOrderMetrics(BaseModel):
    """Additional metrics for concurrent execution"""
    concurrent_groups: int = 0
    max_concurrent_agents: int = 0
    dependency_blocks: int = 0
    batch_failures: int = 0
    agent_timeouts: int = 0

@order_registry.register("concurrent")
class ConcurrentOrder(BaseOrder):
    """Order where all agents act simultaneously"""
    
    name: ClassVar[str] = "concurrent_order"
    description: ClassVar[str] = "Order for concurrent agent execution"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        config: Optional[ConcurrentOrderConfig] = None
    ):
        super().__init__(config=config or ConcurrentOrderConfig())
        self.dependencies: Dict[str, Set[str]] = {}
        self.concurrent_metrics = ConcurrentOrderMetrics()
        
    async def _execute(
        self,
        state: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Execute concurrent order
        
        Args:
            state: Current environment state
            **kwargs: Additional arguments
            
        Returns:
            Updated state
        """
        try:
            # Get available agents
            agents = await self._get_available_agents(state)
            if not agents:
                return state
            
            # Execute agents concurrently
            async with asyncio.TaskGroup() as group:
                tasks = [
                    group.create_task(
                        self._execute_agent(
                            agent_id=agent_id,
                            state=state,
                            **kwargs
                        )
                    )
                    for agent_id in agents
                ]
            
            # Process results
            results = [task.result() for task in tasks]
            
            # Update state with results
            new_state = await self._update_state_with_results(
                state=state,
                results=results,
                agents=agents
            )
            
            # Update metrics
            self._update_concurrent_metrics(len(agents))
            
            return new_state
            
        except Exception as e:
            self.concurrent_metrics.batch_failures += 1
            raise ActionError(
                message=f"Concurrent execution failed: {str(e)}",
                action=self.name,
                details={
                    "agents": list(agents),
                    "state": state
                }
            )
    
    async def _get_available_agents(
        self,
        state: Dict[str, Any]
    ) -> Set[str]:
        """Get available agents for execution
        
        Args:
            state: Current environment state
            
        Returns:
            Set of available agent IDs
        """
        agents = set(state.get("agents", []))
        
        # Apply concurrent limit
        if self.config.max_concurrent > 0:
            agents = set(list(agents)[:self.config.max_concurrent])
        
        # Apply dependency filtering
        if self.config.enforce_dependencies:
            agents = await self._filter_by_dependencies(
                agents,
                state
            )
        
        return agents
    
    async def _filter_by_dependencies(
        self,
        agents: Set[str],
        state: Dict[str, Any]
    ) -> Set[str]:
        """Filter agents based on dependencies
        
        Args:
            agents: Agent IDs to filter
            state: Current state
            
        Returns:
            Filtered agent IDs
        """
        available = set()
        last_agents = set(state.get("last_agents", []))
        
        for agent_id in agents:
            dependencies = self.dependencies.get(agent_id, set())
            if not dependencies or dependencies.issubset(last_agents):
                available.add(agent_id)
            else:
                self.concurrent_metrics.dependency_blocks += 1
        
        return available
    
    async def _execute_agent(
        self,
        agent_id: str,
        state: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Execute single agent
        
        Args:
            agent_id: Agent to execute
            state: Current state
            **kwargs: Additional arguments
            
        Returns:
            Agent execution result
        """
        try:
            # Execute with timeout
            async with asyncio.timeout(self.config.timeout_per_agent):
                result = await self._process_agent(
                    agent_id=agent_id,
                    state=state,
                    **kwargs
                )
                return result
                
        except asyncio.TimeoutError:
            self.concurrent_metrics.agent_timeouts += 1
            logger.warning(f"Agent {agent_id} execution timed out")
            return {
                "agent_id": agent_id,
                "status": "timeout",
                "error": "Execution timed out"
            }
        except Exception as e:
            logger.error(f"Agent {agent_id} execution failed: {str(e)}")
            return {
                "agent_id": agent_id,
                "status": "error",
                "error": str(e)
            }
    
    async def _update_state_with_results(
        self,
        state: Dict[str, Any],
        results: List[Dict[str, Any]],
        agents: Set[str]
    ) -> Dict[str, Any]:
        """Update state with agent results
        
        Args:
            state: Current state
            results: Agent execution results
            agents: Executed agents
            
        Returns:
            Updated state
        """
        new_state = state.copy()
        
        # Update agent states
        for result in results:
            agent_id = result["agent_id"]
            if "error" in result:
                new_state["agent_states"][agent_id] = {
                    "status": result["status"],
                    "error": result["error"],
                    "last_execution": datetime.utcnow().isoformat()
                }
            else:
                new_state["agent_states"][agent_id] = {
                    "status": "completed",
                    "last_execution": datetime.utcnow().isoformat(),
                    **result
                }
        
        # Update execution tracking
        new_state["last_agents"] = list(agents)
        new_state["last_execution"] = datetime.utcnow().isoformat()
        
        return new_state
    
    def add_dependency(
        self,
        agent_id: str,
        depends_on: Set[str]
    ) -> None:
        """Add agent dependencies
        
        Args:
            agent_id: Agent ID
            depends_on: Set of agent IDs this agent depends on
        """
        self.dependencies[agent_id] = depends_on
        logger.debug(
            f"Added dependencies for agent {agent_id}: {depends_on}"
        )
    
    def _update_concurrent_metrics(
        self,
        agent_count: int
    ) -> None:
        """Update concurrent execution metrics
        
        Args:
            agent_count: Number of agents executed
        """
        self.concurrent_metrics.concurrent_groups += 1
        self.concurrent_metrics.max_concurrent_agents = max(
            self.concurrent_metrics.max_concurrent_agents,
            agent_count
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics including concurrent metrics"""
        metrics = super().get_metrics()
        metrics.update(self.concurrent_metrics.model_dump())
        return metrics
    
    def reset(self) -> None:
        """Reset order state"""
        super().reset()
        self.dependencies.clear()
        self.concurrent_metrics = ConcurrentOrderMetrics()
        logger.info(f"Reset {self.name} order and dependencies")

@order_registry.register("concurrent_batched")
class BatchedConcurrentOrder(ConcurrentOrder):
    """Concurrent order with batching"""
    
    name: ClassVar[str] = "batched_concurrent_order"
    description: ClassVar[str] = "Concurrent order with batch processing"
    version: ClassVar[str] = "1.1.0"
    
    class BatchConfig(ConcurrentOrderConfig):
        batch_size: int = 3
        min_batch_size: int = 1
        adaptive_batching: bool = True
        batch_timeout: float = 30.0
    
    def __init__(
        self,
        config: Optional[BatchConfig] = None
    ):
        super().__init__(config=config or self.BatchConfig())
        self.batch_metrics = {
            "total_batches": 0,
            "adaptive_adjustments": 0,
            "batch_sizes": []
        }
    
    async def _get_available_agents(
        self,
        state: Dict[str, Any]
    ) -> Set[str]:
        """Get next batch of agents
        
        Args:
            state: Current state
            
        Returns:
            Set of agent IDs for next batch
        """
        all_agents = set(state.get("agents", []))
        if not all_agents:
            return set()
        
        # Determine batch size
        batch_size = self.config.batch_size
        if self.config.adaptive_batching:
            batch_size = await self._get_adaptive_batch_size(state)
        
        # Get batch
        current_turn = state.get("current_turn", 0)
        start_idx = (current_turn * batch_size) % len(all_agents)
        batch = set(list(all_agents)[start_idx:start_idx + batch_size])
        
        # Apply dependency filtering
        if self.config.enforce_dependencies:
            batch = await self._filter_by_dependencies(batch, state)
        
        # Ensure minimum batch size
        if len(batch) < self.config.min_batch_size:
            remaining = all_agents - set(state.get("last_agents", []))
            batch.update(
                set(list(remaining)[:self.config.min_batch_size - len(batch)])
            )
        
        # Update metrics
        self.batch_metrics["total_batches"] += 1
        self.batch_metrics["batch_sizes"].append(len(batch))
        
        return batch
    
    async def _get_adaptive_batch_size(
        self,
        state: Dict[str, Any]
    ) -> int:
        """Calculate adaptive batch size
        
        Args:
            state: Current state
            
        Returns:
            Calculated batch size
        """
        base_size = self.config.batch_size
        
        # Adjust based on recent performance
        history = state.get("history", [])
        if len(history) >= 3:
            recent = history[-3:]
            success_rate = sum(
                1 for h in recent
                if not h.get("errors")
            ) / len(recent)
            
            if success_rate > 0.8:
                base_size += 1
                self.batch_metrics["adaptive_adjustments"] += 1
            elif success_rate < 0.5:
                base_size = max(
                    self.config.min_batch_size,
                    base_size - 1
                )
                self.batch_metrics["adaptive_adjustments"] += 1
        
        return min(base_size, len(state.get("agents", [])))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics including batch metrics"""
        metrics = super().get_metrics()
        
        if self.batch_metrics["batch_sizes"]:
            metrics.update({
                "avg_batch_size": (
                    sum(self.batch_metrics["batch_sizes"]) /
                    len(self.batch_metrics["batch_sizes"])
                ),
                "total_batches": self.batch_metrics["total_batches"],
                "adaptive_adjustments": self.batch_metrics["adaptive_adjustments"]
            })
        
        return metrics 