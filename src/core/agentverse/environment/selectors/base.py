from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, ClassVar, Set
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging
import re

from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.environment.registry import selector_registry
from src.core.agentverse.message.base import Message
from src.core.agentverse.environment.exceptions import ActionError

logger = logging.getLogger(__name__)

class SelectorConfig(BaseModel):
    """Configuration for message selection"""
    filter_empty: bool = True
    track_filtered: bool = True
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    content_filters: List[str] = Field(default_factory=list)
    regex_filters: List[str] = Field(default_factory=list)
    agent_filters: List[str] = Field(default_factory=list)
    max_selections: Optional[int] = None
    track_metrics: bool = True
    
    model_config = ConfigDict(
        extra="allow"
    )

class SelectionMetrics(BaseModel):
    """Metrics for message selection"""
    total_messages: int = 0
    selected_count: int = 0
    filtered_count: int = 0
    last_selection: datetime = Field(default_factory=datetime.utcnow)
    filters_applied: List[str] = Field(default_factory=list)
    filter_counts: Dict[str, int] = Field(default_factory=dict)
    agent_stats: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    selection_durations: List[float] = Field(default_factory=list)

class BaseSelector(ABC):
    """Base class for message selectors"""
    
    name: ClassVar[str] = "base_selector"
    description: ClassVar[str] = "Base selector implementation"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        config: Optional[SelectorConfig] = None
    ):
        self.config = config or SelectorConfig()
        self.metrics = SelectionMetrics()
        logger.info(f"Initialized {self.name} selector v{self.version}")
    
    async def select_messages(
        self,
        environment: BaseEnvironment,
        messages: List[Message]
    ) -> List[Message]:
        """Select valid messages
        
        Args:
            environment: Environment instance
            messages: Messages to select from
            
        Returns:
            Selected messages
            
        Raises:
            ActionError: If selection fails
        """
        start_time = datetime.utcnow()
        try:
            # Update basic metrics
            self.metrics.total_messages += len(messages)
            
            # Apply basic filters
            filtered = await self._apply_basic_filters(messages)
            
            # Apply custom selection
            selected = await self._select_messages(
                environment=environment,
                messages=filtered
            )
            
            # Apply max selections limit
            if self.config.max_selections:
                selected = selected[:self.config.max_selections]
            
            # Update metrics
            if self.config.track_metrics:
                duration = (datetime.utcnow() - start_time).total_seconds()
                self._update_metrics(messages, filtered, selected, duration)
            
            return selected
            
        except Exception as e:
            logger.error(f"Message selection failed: {str(e)}")
            raise ActionError(
                message=str(e),
                action=self.name,
                details={
                    "messages": len(messages),
                    "filters": self.config.content_filters
                }
            )
    
    @abstractmethod
    async def _select_messages(
        self,
        environment: BaseEnvironment,
        messages: List[Message]
    ) -> List[Message]:
        """Custom message selection logic
        
        Args:
            environment: Environment instance
            messages: Pre-filtered messages
            
        Returns:
            Selected messages
        """
        pass
    
    async def _apply_basic_filters(
        self,
        messages: List[Message]
    ) -> List[Message]:
        """Apply basic message filters
        
        Args:
            messages: Messages to filter
            
        Returns:
            Filtered messages
        """
        filtered = messages
        applied_filters = []
        
        # Filter empty messages
        if self.config.filter_empty:
            filtered = [m for m in filtered if m.content and m.content.strip()]
            if len(filtered) != len(messages):
                applied_filters.append("empty")
                self._increment_filter_count("empty")
        
        # Apply length filters
        if self.config.max_length:
            filtered = [
                m for m in filtered
                if len(m.content) <= self.config.max_length
            ]
            if len(filtered) != len(messages):
                applied_filters.append("max_length")
                self._increment_filter_count("max_length")
                
        if self.config.min_length:
            filtered = [
                m for m in filtered
                if len(m.content) >= self.config.min_length
            ]
            if len(filtered) != len(messages):
                applied_filters.append("min_length")
                self._increment_filter_count("min_length")
        
        # Apply content filters
        for filter_term in self.config.content_filters:
            original_count = len(filtered)
            filtered = [
                m for m in filtered
                if filter_term.lower() not in m.content.lower()
            ]
            if len(filtered) != original_count:
                applied_filters.append(f"content:{filter_term}")
                self._increment_filter_count(f"content:{filter_term}")
        
        # Apply regex filters
        for pattern in self.config.regex_filters:
            original_count = len(filtered)
            regex = re.compile(pattern)
            filtered = [
                m for m in filtered
                if not regex.search(m.content)
            ]
            if len(filtered) != original_count:
                applied_filters.append(f"regex:{pattern}")
                self._increment_filter_count(f"regex:{pattern}")
        
        # Apply agent filters
        if self.config.agent_filters:
            original_count = len(filtered)
            filtered = [
                m for m in filtered
                if m.sender not in self.config.agent_filters
            ]
            if len(filtered) != original_count:
                applied_filters.append("agent")
                self._increment_filter_count("agent")
        
        self.metrics.filters_applied = applied_filters
        return filtered
    
    def _increment_filter_count(self, filter_name: str) -> None:
        """Increment filter application count
        
        Args:
            filter_name: Name of filter applied
        """
        self.metrics.filter_counts[filter_name] = (
            self.metrics.filter_counts.get(filter_name, 0) + 1
        )
    
    def _update_metrics(
        self,
        original: List[Message],
        filtered: List[Message],
        selected: List[Message],
        duration: float
    ) -> None:
        """Update selection metrics
        
        Args:
            original: Original messages
            filtered: Filtered messages
            selected: Selected messages
            duration: Selection duration
        """
        self.metrics.selected_count += len(selected)
        self.metrics.filtered_count += len(original) - len(filtered)
        self.metrics.last_selection = datetime.utcnow()
        self.metrics.selection_durations.append(duration)
        
        # Update agent stats
        for message in selected:
            if message.sender:
                stats = self.metrics.agent_stats.setdefault(
                    message.sender,
                    {"total": 0, "selected": 0, "filtered": 0}
                )
                stats["total"] += 1
                stats["selected"] += 1
        
        for message in filtered:
            if message.sender:
                stats = self.metrics.agent_stats.setdefault(
                    message.sender,
                    {"total": 0, "selected": 0, "filtered": 0}
                )
                stats["filtered"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get selector metrics
        
        Returns:
            Selection metrics
        """
        metrics = self.metrics.model_dump()
        
        # Add average duration
        if self.metrics.selection_durations:
            metrics["avg_duration"] = (
                sum(self.metrics.selection_durations) /
                len(self.metrics.selection_durations)
            )
        
        # Add selection rate
        if self.metrics.total_messages > 0:
            metrics["selection_rate"] = (
                self.metrics.selected_count /
                self.metrics.total_messages
            )
        
        return metrics
    
    def reset(self) -> None:
        """Reset selector state"""
        self.metrics = SelectionMetrics()
        logger.info(f"Reset {self.name} selector")

@selector_registry.register("basic")
class BasicSelector(BaseSelector):
    """Basic message selector"""
    
    name: ClassVar[str] = "basic_selector"
    description: ClassVar[str] = "Basic pass-through message selector"
    version: ClassVar[str] = "1.1.0"
    
    async def _select_messages(
        self,
        environment: BaseEnvironment,
        messages: List[Message]
    ) -> List[Message]:
        """Pass through valid messages
        
        Args:
            environment: Environment instance
            messages: Pre-filtered messages
            
        Returns:
            Selected messages
        """
        return messages

@selector_registry.register("latest")
class LatestSelector(BaseSelector):
    """Select only the most recent messages"""
    
    name: ClassVar[str] = "latest_selector"
    description: ClassVar[str] = "Selector for most recent messages"
    version: ClassVar[str] = "1.1.0"
    
    class LatestConfig(SelectorConfig):
        window_size: int = 5
    
    def __init__(
        self,
        config: Optional[LatestConfig] = None
    ):
        super().__init__(config=config or self.LatestConfig())
    
    async def _select_messages(
        self,
        environment: BaseEnvironment,
        messages: List[Message]
    ) -> List[Message]:
        """Get most recent messages
        
        Args:
            environment: Environment instance
            messages: Pre-filtered messages
            
        Returns:
            Selected messages
        """
        return messages[-self.config.window_size:]

@selector_registry.register("agent_specific")
class AgentSelector(BaseSelector):
    """Select messages for specific agents"""
    
    name: ClassVar[str] = "agent_selector"
    description: ClassVar[str] = "Selector for agent-specific messages"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        agent_ids: List[str],
        config: Optional[SelectorConfig] = None
    ):
        super().__init__(config=config)
        self.agent_ids = set(agent_ids)
    
    async def _select_messages(
        self,
        environment: BaseEnvironment,
        messages: List[Message]
    ) -> List[Message]:
        """Get agent-specific messages
        
        Args:
            environment: Environment instance
            messages: Pre-filtered messages
            
        Returns:
            Selected messages
        """
        return [
            m for m in messages
            if m.sender in self.agent_ids or
            any(aid in m.receiver for aid in self.agent_ids)
        ] 