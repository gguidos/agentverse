from abc import ABC, abstractmethod
from typing import Dict, Set, Any, Optional, ClassVar, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging

from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.environment.exceptions import ActionError

logger = logging.getLogger(__name__)

class VisibilityConfig(BaseModel):
    """Configuration for visibility handlers"""
    track_changes: bool = True
    validate_visibility: bool = True
    update_interval: int = 1
    cache_visibility: bool = True
    max_cache_age: float = 60.0  # seconds
    
    model_config = ConfigDict(
        extra="allow"
    )

class VisibilityMetrics(BaseModel):
    """Metrics for visibility updates"""
    total_updates: int = 0
    visibility_changes: int = 0
    last_update: datetime = Field(default_factory=datetime.utcnow)
    update_durations: List[float] = Field(default_factory=list)
    agent_stats: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    cache_hits: int = 0
    cache_misses: int = 0

class VisibilityState(BaseModel):
    """State of visibility handler"""
    visibility_map: Dict[str, Set[str]] = Field(default_factory=dict)
    last_update: Optional[datetime] = None
    cache_valid: bool = False
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

class BaseVisibility(ABC):
    """Base class for visibility handlers"""
    
    name: ClassVar[str] = "base_visibility"
    description: ClassVar[str] = "Base visibility handler implementation"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        config: Optional[VisibilityConfig] = None
    ):
        self.config = config or VisibilityConfig()
        self.state = VisibilityState()
        self.metrics = VisibilityMetrics()
        logger.info(f"Initialized {self.name} visibility handler v{self.version}")
    
    async def update_visible_agents(
        self,
        environment: BaseEnvironment
    ) -> None:
        """Update which agents can see each other
        
        Args:
            environment: Environment to update visibility for
            
        Raises:
            ActionError: If visibility update fails
        """
        start_time = datetime.utcnow()
        try:
            # Check if update needed
            if not self._should_update(environment):
                if self.config.cache_visibility:
                    self.metrics.cache_hits += 1
                return
            
            if self.config.cache_visibility:
                self.metrics.cache_misses += 1
            
            # Store old visibility for change tracking
            old_visibility = self.state.visibility_map.copy() if self.config.track_changes else {}
            
            # Update visibility
            await self._update_visibility(environment)
            
            # Validate if configured
            if self.config.validate_visibility:
                self._validate_visibility(environment)
            
            # Track changes if configured
            if self.config.track_changes:
                self._track_changes(old_visibility)
            
            # Update state
            self.state.last_update = datetime.utcnow()
            self.state.cache_valid = True
            
            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(duration)
            
        except Exception as e:
            logger.error(f"Visibility update failed: {str(e)}")
            raise ActionError(
                message=str(e),
                action=self.name,
                details={
                    "environment": environment.name,
                    "agents": len(environment.agents)
                }
            )
    
    def _should_update(
        self,
        environment: BaseEnvironment
    ) -> bool:
        """Check if visibility update is needed
        
        Args:
            environment: Environment to check
            
        Returns:
            Whether update is needed
        """
        if not self.config.cache_visibility:
            return True
            
        if not self.state.cache_valid:
            return True
            
        if not self.state.last_update:
            return True
            
        # Check cache age
        age = (datetime.utcnow() - self.state.last_update).total_seconds()
        if age > self.config.max_cache_age:
            return True
            
        # Check update interval
        return (
            environment.state.current_turn % self.config.update_interval == 0
        )
    
    @abstractmethod
    async def _update_visibility(
        self,
        environment: BaseEnvironment
    ) -> None:
        """Update visibility implementation
        
        Args:
            environment: Environment to update visibility for
        """
        pass
    
    def _validate_visibility(
        self,
        environment: BaseEnvironment
    ) -> None:
        """Validate visibility configuration
        
        Args:
            environment: Environment to validate
            
        Raises:
            ActionError: If validation fails
        """
        agent_names = {agent.name for agent in environment.agents}
        
        # Check all agents have visibility entries
        missing = agent_names - set(self.state.visibility_map.keys())
        if missing:
            raise ActionError(
                message="Missing visibility entries",
                action=self.name,
                details={"missing": list(missing)}
            )
        
        # Check visibility targets are valid
        for agent, visible in self.state.visibility_map.items():
            invalid = visible - agent_names
            if invalid:
                raise ActionError(
                    message=f"Invalid visibility targets for {agent}",
                    action=self.name,
                    details={"invalid": list(invalid)}
                )
    
    def _track_changes(
        self,
        old_visibility: Dict[str, Set[str]]
    ) -> None:
        """Track visibility changes
        
        Args:
            old_visibility: Previous visibility state
        """
        for agent, new_visible in self.state.visibility_map.items():
            old_visible = old_visibility.get(agent, set())
            
            # Track added/removed visibility
            added = new_visible - old_visible
            removed = old_visible - new_visible
            
            if added or removed:
                self.metrics.visibility_changes += 1
                
                # Update agent stats
                stats = self.metrics.agent_stats.setdefault(
                    agent,
                    {"changes": 0, "added": 0, "removed": 0}
                )
                stats["changes"] += 1
                stats["added"] += len(added)
                stats["removed"] += len(removed)
    
    def _update_metrics(
        self,
        duration: float
    ) -> None:
        """Update tracking metrics
        
        Args:
            duration: Update duration
        """
        self.metrics.total_updates += 1
        self.metrics.last_update = datetime.utcnow()
        self.metrics.update_durations.append(duration)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get visibility metrics
        
        Returns:
            Visibility metrics
        """
        metrics = self.metrics.model_dump()
        
        # Add average duration
        if self.metrics.update_durations:
            metrics["avg_duration"] = (
                sum(self.metrics.update_durations) /
                len(self.metrics.update_durations)
            )
        
        # Add cache stats
        total_checks = self.metrics.cache_hits + self.metrics.cache_misses
        if total_checks > 0:
            metrics["cache_hit_rate"] = (
                self.metrics.cache_hits / total_checks
            )
        
        return metrics
    
    def is_visible(
        self,
        viewer: str,
        target: str
    ) -> bool:
        """Check if target is visible to viewer
        
        Args:
            viewer: Agent checking visibility
            target: Agent to check visibility of
            
        Returns:
            Whether target is visible to viewer
        """
        return target in self.state.visibility_map.get(viewer, set())
    
    def reset(self) -> None:
        """Reset visibility state"""
        self.state = VisibilityState()
        self.metrics = VisibilityMetrics()
        logger.info(f"Reset {self.name} visibility handler")
    
    def __str__(self) -> str:
        return f"{self.name}Visibility(v{self.version})"
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"updates={self.metrics.total_updates}, "
            f"changes={self.metrics.visibility_changes})"
        ) 