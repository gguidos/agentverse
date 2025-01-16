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
from src.core.agentverse.recovery import RetryHandler, RetryConfig
from src.core.infrastructure.circuit_breaker import circuit_breaker
from src.core.agentverse.resources import ResourceManager

logger = logging.getLogger(__name__)

class AgentVerseConfig(BaseModel):
    """Configuration for AgentVerse"""
    max_steps: Optional[int] = None
    auto_reset: bool = True
    track_metrics: bool = True
    validate_agents: bool = True
    save_history: bool = True
    output_dir: Path = Field(default=Path("output"))
    retry: RetryConfig = Field(default_factory=RetryConfig)
    enable_recovery: bool = True
    
    # Resource limits
    llm_rate_limit: int = 100  # Calls per minute
    llm_burst_limit: int = 20
    embedding_rate_limit: int = 1000  # Calls per minute
    memory_quota: float = 1024 * 1024 * 1024  # 1GB
    max_concurrent_tasks: int = 10
    
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
        
        # Initialize recovery mechanisms
        if self.config.enable_recovery:
            self.retry = RetryHandler(config=self.config.retry)
        
        # Initialize resource manager
        self.resources = ResourceManager()
        
        # Add rate limiters
        self.resources.add_rate_limiter(
            "llm_calls",
            rate=self.config.llm_rate_limit,
            burst=self.config.llm_burst_limit
        )
        self.resources.add_rate_limiter(
            "embeddings",
            rate=self.config.embedding_rate_limit
        )
        
        # Add quotas
        self.resources.add_quota(
            "memory",
            max_usage=self.config.memory_quota,
            unit="bytes",
            reset_interval=3600  # Reset hourly
        )
        self.resources.add_quota(
            "concurrent_tasks",
            max_usage=self.config.max_concurrent_tasks
        )
    
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
        """Run environment with recovery mechanisms"""
        if not self.config.enable_recovery:
            return await self._run_without_recovery()
            
        try:
            if self.config.auto_reset:
                await self.retry.wrap(self.reset)()
            
            while not self._should_stop():
                # Use existing circuit breaker with retry
                result = await circuit_breaker(self.retry.wrap(self.step))()
                
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
    
    async def _handle_circuit_open(self) -> None:
        """Handle circuit breaker open state"""
        try:
            # Try to save state
            await self._save_state()
            # Notify monitoring
            if self.monitor:
                self.monitor.alert("circuit_breaker_open")
        except Exception as e:
            logger.error(f"Failed to handle circuit open: {str(e)}")
    
    async def _handle_run_error(self, error: Exception) -> None:
        """Handle run errors"""
        try:
            # Save error state
            await self._save_state()
            # Record error metrics
            if self.monitor:
                self.monitor.track_error(
                    agent_id="environment",
                    error_type=error.__class__.__name__,
                    error=str(error)
                )
        except Exception as e:
            logger.error(f"Failed to handle run error: {str(e)}")
    
    async def step(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute step with resource management"""
        # Check concurrent task quota
        if not await self.resources.check_quota("concurrent_tasks", 1):
            raise AgentVerseError("Maximum concurrent tasks exceeded")
        
        try:
            # Use rate limiter for step execution
            async with self.resources.rate_limiters["llm_calls"]:
                result = await super().step(*args, **kwargs)
            
            return result
            
        finally:
            # Release task quota
            await self.resources.check_quota("concurrent_tasks", -1)
    
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
        """Get metrics including resource usage"""
        metrics = super().get_metrics()
        metrics["resources"] = self.resources.get_metrics()
        return metrics 