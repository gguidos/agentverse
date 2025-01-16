"""
Task orchestration implementation
"""

import logging
from typing import Any, Dict, List, Optional

from src.core.agentverse.message import Message
from src.core.agentverse.agents import BaseAgent
from src.core.agentverse.system import TaskConfig
from src.core.agentverse.exceptions import TaskError

logger = logging.getLogger(__name__)

class TaskOrchestrator:
    """Orchestrates task execution across agents"""
    
    def __init__(
        self,
        config: TaskConfig,
        agents: List[BaseAgent],
        **kwargs
    ):
        """Initialize orchestrator
        
        Args:
            config: Task configuration
            agents: List of agents
            **kwargs: Additional arguments
        """
        self.config = config
        self.agents = agents
        self.steps = 0
        self.history: List[Dict[str, Any]] = []
    
    async def execute_task(self) -> Dict[str, Any]:
        """Execute configured task
        
        Returns:
            Task results
            
        Raises:
            TaskError: If execution fails
        """
        try:
            logger.info(f"Starting task: {self.config.name}")
            
            # Initialize task state
            state = {
                "task": self.config.name,
                "step": 0,
                "complete": False,
                "results": {}
            }
            
            # Execute task steps
            while not state["complete"] and state["step"] < self.config.environment.get("max_steps", 100):
                state = await self._execute_step(state)
                self.steps += 1
                
            logger.info(f"Task complete: {self.config.name}")
            return state["results"]
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            raise TaskError(
                message="Task execution failed",
                details={
                    "task": self.config.name,
                    "step": self.steps,
                    "error": str(e)
                }
            )
    
    async def _execute_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute single task step
        
        Args:
            state: Current task state
            
        Returns:
            Updated task state
            
        Raises:
            TaskError: If step execution fails
        """
        try:
            # Get next agent
            agent = self._get_next_agent(state)
            
            # Create step message
            message = Message.system(
                content=f"Execute step {state['step']} of task {self.config.name}",
                metadata={"state": state}
            )
            
            # Process message
            response = await agent.process_message(message)
            
            # Update state
            state["step"] += 1
            state["results"][f"step_{state['step']}"] = {
                "agent": agent.name,
                "response": response.content
            }
            
            # Check completion
            state["complete"] = self._check_completion(state)
            
            # Store history
            self.history.append({
                "step": state["step"],
                "agent": agent.name,
                "message": message,
                "response": response
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            raise TaskError(
                message="Step execution failed",
                details={
                    "step": state["step"],
                    "error": str(e)
                }
            )
    
    def _get_next_agent(self, state: Dict[str, Any]) -> BaseAgent:
        """Get next agent for task step
        
        Args:
            state: Current task state
            
        Returns:
            Next agent to execute
            
        Raises:
            TaskError: If no agent available
        """
        try:
            # Simple round-robin for now
            agent_index = state["step"] % len(self.agents)
            return self.agents[agent_index]
        except Exception as e:
            raise TaskError(
                message="Failed to get next agent",
                details={"error": str(e)}
            )
    
    def _check_completion(self, state: Dict[str, Any]) -> bool:
        """Check if task is complete
        
        Args:
            state: Current task state
            
        Returns:
            Whether task is complete
        """
        # Add custom completion logic here
        return False 