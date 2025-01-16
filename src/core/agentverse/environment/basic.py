from typing import Dict, Any, List, Optional, Set
import asyncio
import logging
from datetime import datetime

from src.core.agentverse.environment.base import BaseEnvironment, EnvironmentState
from src.core.agentverse.environment.rules import Rule, RuleConfig
from src.core.agentverse.environment.registry import env_registry
from src.core.agentverse.message.base import Message
from src.core.agentverse.environment.exceptions import EnvironmentError

logger = logging.getLogger(__name__)

class BasicEnvironmentState(EnvironmentState):
    """State model for basic environment"""
    
    # Turn management
    current_turn: int = 0
    max_turns: Optional[int] = None
    
    # Message tracking
    last_messages: List[Message] = []
    message_history: List[Message] = []
    
    # Agent state
    agent_states: Dict[str, Dict[str, Any]] = {}
    agent_order: List[str] = []
    
    # Performance tracking
    step_durations: List[float] = []
    rule_applications: Dict[str, int] = {}

@env_registry.register("basic")
class BasicEnvironment(BaseEnvironment):
    """Basic environment with configurable rules"""
    
    name: str = "basic_environment"
    description: str = "Basic environment with turn-based agent interactions"
    version: str = "1.1.0"
    
    def __init__(
        self,
        rule_config: Dict[str, Any],
        **kwargs
    ):
        # Configure rules
        rule = self._setup_rules(rule_config)
        state = BasicEnvironmentState()
        super().__init__(rule=rule, state=state, **kwargs)
        
        # Initialize metrics
        self.state.metrics.update({
            "messages_processed": 0,
            "rules_applied": 0,
            "avg_step_duration": 0.0,
            "total_steps": 0
        })
        
        logger.info(f"Initialized basic environment with rules: {rule_config}")
    
    def _setup_rules(self, config: Dict[str, Any]) -> Rule:
        """Set up environment rules
        
        Args:
            config: Rule configuration
            
        Returns:
            Rule: Configured rule instance
            
        Raises:
            EnvironmentError: If rule setup fails
        """
        try:
            rule_config = RuleConfig(
                order=config.get("order", {"type": "sequential"}),
                visibility=config.get("visibility", {"type": "all"}),
                selector=config.get("selector", {"type": "basic"}),
                updater=config.get("updater", {"type": "basic"}),
                describer=config.get("describer", {"type": "basic"})
            )
            
            return Rule(
                order_config=rule_config.order,
                visibility_config=rule_config.visibility,
                selector_config=rule_config.selector,
                updater_config=rule_config.updater,
                describer_config=rule_config.describer
            )
            
        except Exception as e:
            raise EnvironmentError(f"Failed to setup rules: {str(e)}")
    
    async def step(self) -> Dict[str, Any]:
        """Execute one environment step
        
        Returns:
            Dict containing step results
            
        Raises:
            EnvironmentError: If step execution fails
        """
        try:
            # Validate state
            if not await self.validate_state():
                raise EnvironmentError("Invalid environment state")
            
            # Update state
            self.state.status = "processing"
            step_start = datetime.utcnow()
            
            # Get next agents
            next_agents = await self._get_next_agents()
            if not next_agents:
                raise EnvironmentError("No agents selected for step")
            
            # Get environment descriptions
            descriptions = await self._get_descriptions(next_agents)
            
            # Process agent turns concurrently
            async with asyncio.TaskGroup() as group:
                message_tasks = [
                    group.create_task(
                        self._process_agent_turn(
                            agent_id=agent_id,
                            description=descriptions[agent_id]
                        )
                    )
                    for agent_id in next_agents
                ]
            
            messages = [task.result() for task in message_tasks]
            
            # Select and process messages
            selected_messages = await self._select_messages(messages)
            
            # Update state
            await self._update_after_step(selected_messages)
            
            # Calculate step duration
            duration = (datetime.utcnow() - step_start).total_seconds()
            self._update_step_metrics(duration, len(selected_messages))
            
            return {
                "messages": selected_messages,
                "state": self.state.dict(),
                "is_done": await self.is_done(),
                "metrics": self.state.metrics
            }
            
        except Exception as e:
            self.state.status = "error"
            self.state.error_count += 1
            logger.error(f"Environment step failed: {str(e)}")
            raise EnvironmentError(f"Step failed: {str(e)}")
    
    async def _get_next_agents(self) -> Set[str]:
        """Get next agents to act"""
        agents = await self.rule.get_next_agents(self.state)
        return set(agents) & self.state.agents
    
    async def _get_descriptions(self, agent_ids: Set[str]) -> Dict[str, str]:
        """Get environment descriptions for agents"""
        return {
            agent_id: await self.rule.get_description(
                agent_id,
                self.state
            )
            for agent_id in agent_ids
        }
    
    async def _process_agent_turn(
        self,
        agent_id: str,
        description: str
    ) -> Message:
        """Process single agent turn
        
        Args:
            agent_id: Agent ID
            description: Environment description
            
        Returns:
            Message: Agent's response
            
        Raises:
            EnvironmentError: If processing fails
        """
        try:
            async with self._locks[agent_id]:
                message = await self.rule.process_agent_turn(
                    agent_id=agent_id,
                    description=description,
                    state=self.state
                )
                return message
                
        except Exception as e:
            logger.error(f"Agent {agent_id} turn failed: {str(e)}")
            raise EnvironmentError(f"Agent turn failed: {str(e)}")
    
    async def _select_messages(self, messages: List[Message]) -> List[Message]:
        """Select messages to process"""
        return await self.rule.select_messages(
            messages=messages,
            state=self.state
        )
    
    async def _update_after_step(self, messages: List[Message]) -> None:
        """Update state after step completion"""
        # Update message history
        self.state.last_messages = messages
        self.state.message_history.extend(messages)
        
        # Update turn counter
        self.state.current_turn += 1
        
        # Update status
        self.state.status = "completed"
        self.state.last_update = datetime.utcnow()
    
    def _update_step_metrics(self, duration: float, message_count: int) -> None:
        """Update metrics after step"""
        metrics = self.state.metrics
        
        # Update counts
        metrics["total_steps"] += 1
        metrics["messages_processed"] += message_count
        
        # Update duration metrics
        metrics["avg_step_duration"] = (
            (metrics["avg_step_duration"] * (metrics["total_steps"] - 1) + duration)
            / metrics["total_steps"]
        )
        
        # Store duration
        self.state.step_durations.append(duration)
    
    async def is_done(self) -> bool:
        """Check if environment is done"""
        if self.state.max_turns and self.state.current_turn >= self.state.max_turns:
            return True
            
        return await self.rule.is_done(self.state) 