"""Simulation Module"""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from src.core.agentverse.config import load_config
from src.core.agentverse.initialization import load_agent_config, load_environment_config
from src.core.agentverse.exceptions import SimulationError
from src.core.agentverse.agents import BaseAgent
from src.core.agentverse.environment import BaseEnvironment, EnvironmentStepResult
from .config import SimulationConfig

logger = logging.getLogger(__name__)

class Simulation:
    """Simulation class"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize simulation"""
        self.config = SimulationConfig(**config)
        self.agents: List[BaseAgent] = []
        self.environment: Optional[BaseEnvironment] = None
        self.history: List[EnvironmentStepResult] = []
        self._load_components()
    
    def _load_components(self):
        """Load simulation components"""
        try:
            # Load environment
            self.environment = load_environment_config(self.config.environment)
            
            # Load agents
            for agent_config in self.config.agents:
                agent = load_agent_config(agent_config)
                self.agents.append(agent)
                # Register agent with environment
                if hasattr(self.environment, 'add_agent'):
                    self.environment.add_agent(agent)
            
        except Exception as e:
            logger.error(f"Failed to load components: {str(e)}")
            raise SimulationError(f"Failed to load components: {str(e)}")
    
    async def step(self) -> EnvironmentStepResult:
        """Execute one simulation step"""
        if not self.environment:
            raise SimulationError("Environment not initialized")
            
        result = await self.environment.step()
        if self.config.save_history:
            self.history.append(result)
        return result
    
    async def run(self) -> List[EnvironmentStepResult]:
        """Run full simulation"""
        results = []
        for _ in range(self.config.max_steps):
            result = await self.step()
            results.append(result)
            if result.done:
                break
        return results
    
    async def reset(self):
        """Reset simulation state"""
        if self.environment:
            await self.environment.reset()
        self.history.clear()
    
    @classmethod
    async def from_task(cls, task_name: str, tasks_dir: str) -> "Simulation":
        """Create simulation from task config"""
        try:
            # Load task config
            config = load_config(task_name, tasks_dir)
            
            # Create simulation
            return cls(config)
            
        except Exception as e:
            logger.error(f"Failed to create simulation: {str(e)}")
            raise SimulationError(f"Failed to create simulation: {str(e)}") 