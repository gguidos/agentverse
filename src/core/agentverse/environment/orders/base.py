from typing import Dict, Any, Optional, ClassVar, List
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging

from src.core.agentverse.environment.registry import order_registry
from src.core.agentverse.environment.exceptions import ActionError

logger = logging.getLogger(__name__)

class OrderConfig(BaseModel):
    """Configuration for environment orders"""
    validate_before_execute: bool = True
    track_execution: bool = True
    max_retries: int = 3
    timeout: float = 30.0
    
    model_config = ConfigDict(
        extra="allow"
    )

class OrderMetrics(BaseModel):
    """Metrics for order execution"""
    executions: int = 0
    failures: int = 0
    last_execution: Optional[datetime] = None
    execution_times: List[float] = Field(default_factory=list)
    retry_counts: List[int] = Field(default_factory=list)

class OrderResult(BaseModel):
    """Result of order execution"""
    success: bool = True
    state: Dict[str, Any]
    changes: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float = 0.0
    retries: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class BaseOrder(ABC):
    """Base class for environment orders"""
    
    name: ClassVar[str] = "base_order"
    description: ClassVar[str] = "Base order implementation"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        config: Optional[OrderConfig] = None
    ):
        self.config = config or OrderConfig()
        self.metrics = OrderMetrics()
        logger.info(f"Initialized {self.name} order v{self.version}")
    
    async def execute(
        self,
        state: Dict[str, Any],
        **kwargs
    ) -> OrderResult:
        """Execute the order and return updated state
        
        Args:
            state: Current environment state
            **kwargs: Additional execution arguments
            
        Returns:
            OrderResult containing execution results
            
        Raises:
            ActionError: If execution fails
        """
        start_time = datetime.utcnow()
        retries = 0
        
        try:
            # Validate state if configured
            if self.config.validate_before_execute:
                if not await self.validate(state):
                    raise ValueError("Invalid state for order execution")
            
            # Execute with retries
            while retries < self.config.max_retries:
                try:
                    # Execute order
                    new_state = await self._execute(state, **kwargs)
                    
                    # Track changes
                    changes = self._track_state_changes(state, new_state)
                    
                    # Create result
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    result = OrderResult(
                        success=True,
                        state=new_state,
                        changes=changes,
                        execution_time=duration,
                        retries=retries,
                        metadata={
                            "order": self.name,
                            "version": self.version,
                            **kwargs
                        }
                    )
                    
                    # Update metrics
                    if self.config.track_execution:
                        self._update_metrics(duration, retries)
                    
                    return result
                    
                except Exception as e:
                    retries += 1
                    if retries >= self.config.max_retries:
                        raise
                    logger.warning(
                        f"Order execution failed (attempt {retries}): {str(e)}"
                    )
            
        except Exception as e:
            self.metrics.failures += 1
            logger.error(f"Order execution failed: {str(e)}")
            raise ActionError(
                message=str(e),
                action=self.name,
                details={
                    "state": state,
                    "retries": retries,
                    "duration": (datetime.utcnow() - start_time).total_seconds()
                }
            )
    
    @abstractmethod
    async def _execute(
        self,
        state: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Execute order implementation
        
        Args:
            state: Current environment state
            **kwargs: Additional execution arguments
            
        Returns:
            Updated state
        """
        pass
    
    @abstractmethod
    async def validate(
        self,
        state: Dict[str, Any]
    ) -> bool:
        """Validate if order can be executed in current state
        
        Args:
            state: Current environment state
            
        Returns:
            Whether state is valid for execution
        """
        return True
    
    def _track_state_changes(
        self,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track changes between states
        
        Args:
            old_state: Previous state
            new_state: Updated state
            
        Returns:
            Dict of changes
        """
        changes = {}
        
        # Track added/modified keys
        for key, new_value in new_state.items():
            if key not in old_state:
                changes[f"added_{key}"] = new_value
            elif old_state[key] != new_value:
                changes[f"modified_{key}"] = {
                    "old": old_state[key],
                    "new": new_value
                }
        
        # Track removed keys
        for key in old_state:
            if key not in new_state:
                changes[f"removed_{key}"] = old_state[key]
        
        return changes
    
    def _update_metrics(
        self,
        duration: float,
        retries: int
    ) -> None:
        """Update order metrics
        
        Args:
            duration: Execution duration
            retries: Number of retries
        """
        self.metrics.executions += 1
        self.metrics.execution_times.append(duration)
        self.metrics.retry_counts.append(retries)
        self.metrics.last_execution = datetime.utcnow()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get order execution metrics"""
        metrics = self.metrics.model_dump()
        if self.metrics.execution_times:
            metrics["avg_execution_time"] = (
                sum(self.metrics.execution_times) /
                len(self.metrics.execution_times)
            )
            metrics["avg_retries"] = (
                sum(self.metrics.retry_counts) /
                len(self.metrics.retry_counts)
            )
        return metrics
    
    def reset(self) -> None:
        """Reset order state"""
        self.metrics = OrderMetrics()
        logger.info(f"Reset {self.name} order")
    
    def __str__(self) -> str:
        return f"{self.name}Order(v{self.version})"
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"executions={self.metrics.executions}, "
            f"failures={self.metrics.failures})"
        ) 