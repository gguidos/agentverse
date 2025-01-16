from typing import List, Dict, Any, Optional, Tuple, ClassVar
from pydantic import BaseModel, Field, ConfigDict
from pathlib import Path
import asyncio
import logging

from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.system.task_loader import TaskLoader
from src.core.agentverse.exceptions import AgentVerseError
from src.core.agentverse.monitoring.agent_monitor import AgentMonitor

logger = logging.getLogger(__name__)

class AgentVerseConfig(BaseModel):
    """Configuration for AgentVerse"""
    max_steps: Optional[int] = None
    auto_reset: bool = True
    track_metrics: bool = True
    validate_agents: bool = True
    save_history: bool = True
    output_dir: Path = Field(default=Path("output"))
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

class AgentVerse:
    """Main orchestrator for agent environments"""
    
    name: ClassVar[str] = "agentverse"
    description: ClassVar[str] = "Multi-agent environment orchestrator"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        agents: List[BaseAgent],
        environment: BaseEnvironment,
        config: Optional[AgentVerseConfig] = None,
        monitor: Optional[AgentMonitor] = None
    ):
        """Initialize AgentVerse
        
        Args:
            agents: List of agents
            environment: Environment instance
            config: Optional configuration
            monitor: Optional agent monitor
        """
        self.agents = agents
        self.environment = environment
        self.config = config or AgentVerseConfig()
        self.monitor = monitor
        self.step_count = 0
        self.history: List[Dict[str, Any]] = []
        logger.info(f"Initialized {self.name} v{self.version}")
    
    @classmethod
    async def from_task(
        cls,
        task_name: str,
        task_loader: TaskLoader,
        config: Optional[AgentVerseConfig] = None
    ) -> Tuple['AgentVerse', Path]:
        """Create AgentVerse from task configuration
        
        Args:
            task_name: Task identifier
            task_loader: Task loader instance
            config: Optional configuration
            
        Returns:
            Tuple of (AgentVerse instance, output path)
            
        Raises:
            AgentVerseError: If creation fails
        """
        try:
            # Load task configuration
            task_config = await task_loader.load_task(task_name)
            
            # Create agents
            agents = await task_loader.create_agents(
                task_config.get("agents", [])
            )
            
            # Create environment
            env_config = task_config.get("environment", {})
            env_config["agents"] = agents
            environment = await task_loader.create_environment(env_config)
            
            # Create monitor if configured
            monitor = None
            if config and config.track_metrics:
                monitor = AgentMonitor(namespace=task_name)
            
            # Create instance
            instance = cls(
                agents=agents,
                environment=environment,
                config=config,
                monitor=monitor
            )
            
            output_path = (
                config.output_dir if config
                else Path(task_config.get("output_dir", "output"))
            )
            return instance, output_path
            
        except Exception as e:
            logger.error(f"Failed to create AgentVerse from task: {str(e)}")
            raise AgentVerseError(
                message=f"Task initialization failed: {str(e)}",
                details={
                    "task": task_name,
                    "agents": len(task_config.get("agents", []))
                }
            )
    
    async def run(self) -> List[Dict[str, Any]]:
        """Run environment until completion
        
        Returns:
            List of step results
            
        Raises:
            AgentVerseError: If run fails
        """
        try:
            if self.config.auto_reset:
                await self.reset()
            
            while not self._should_stop():
                result = await self.step()
                if self.config.save_history:
                    self.history.append(result)
                
            return self.history if self.config.save_history else []
            
        except Exception as e:
            logger.error(f"Environment run failed: {str(e)}")
            raise AgentVerseError(
                message=f"Run failed: {str(e)}",
                details={
                    "steps": self.step_count,
                    "agents": len(self.agents)
                }
            )
    
    async def step(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute one environment step
        
        Returns:
            Step result
            
        Raises:
            AgentVerseError: If step fails
        """
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Execute step
            result = await self.environment.step(*args, **kwargs)
            self.step_count += 1
            
            # Track metrics
            if self.monitor and self.config.track_metrics:
                duration = asyncio.get_event_loop().time() - start_time
                self.monitor.track_task(
                    agent_id="environment",
                    status="success",
                    duration=duration
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Environment step failed: {str(e)}")
            if self.monitor:
                self.monitor.track_error(
                    agent_id="environment",
                    error_type="step_error",
                    error=str(e)
                )
            raise AgentVerseError(
                message=f"Step failed: {str(e)}",
                details={"step": self.step_count}
            )
    
    async def reset(self) -> None:
        """Reset environment and agents
        
        Raises:
            AgentVerseError: If reset fails
        """
        try:
            # Reset components
            await self.environment.reset()
            for agent in self.agents:
                await agent.reset()
            
            # Reset state
            self.step_count = 0
            self.history.clear()
            
            logger.info(f"Reset {self.name}")
            
        except Exception as e:
            logger.error(f"Reset failed: {str(e)}")
            raise AgentVerseError(
                message=f"Reset failed: {str(e)}",
                details={"agents": len(self.agents)}
            )
    
    def _should_stop(self) -> bool:
        """Check if execution should stop
        
        Returns:
            Whether to stop
        """
        if self.environment.is_done():
            return True
            
        if (
            self.config.max_steps and
            self.step_count >= self.config.max_steps
        ):
            return True
            
        return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics
        
        Returns:
            Metrics dictionary
        """
        metrics = {
            "steps": self.step_count,
            "agents": len(self.agents),
            "history_size": len(self.history)
        }
        
        if self.monitor:
            metrics.update(self.monitor.get_metrics())
            
        return metrics 