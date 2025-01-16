from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, ClassVar, Set
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging
import asyncio

from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.environment.registry import updater_registry
from src.core.agentverse.message.base import Message
from src.core.agentverse.environment.exceptions import ActionError

logger = logging.getLogger(__name__)

class UpdaterConfig(BaseModel):
    """Configuration for memory updates"""
    batch_size: int = 10
    track_updates: bool = True
    max_history: Optional[int] = None
    update_interval: int = 1  # Update every N turns
    concurrent_updates: bool = True
    timeout_per_batch: float = 30.0
    retry_failed: bool = True
    max_retries: int = 3
    
    model_config = ConfigDict(
        extra="allow"
    )

class UpdateMetrics(BaseModel):
    """Metrics for memory updates"""
    total_updates: int = 0
    messages_processed: int = 0
    failed_updates: int = 0
    last_update: datetime = Field(default_factory=datetime.utcnow)
    update_durations: List[float] = Field(default_factory=list)
    batch_sizes: List[int] = Field(default_factory=list)
    agent_stats: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    retry_counts: List[int] = Field(default_factory=list)

class BaseUpdater(ABC):
    """Base class for memory updaters"""
    
    name: ClassVar[str] = "base_updater"
    description: ClassVar[str] = "Base updater implementation"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        config: Optional[UpdaterConfig] = None
    ):
        self.config = config or UpdaterConfig()
        self.metrics = UpdateMetrics()
        logger.info(f"Initialized {self.name} updater v{self.version}")
    
    async def update_memory(
        self,
        environment: BaseEnvironment
    ) -> None:
        """Update agent memories
        
        Args:
            environment: Environment to update
            
        Raises:
            ActionError: If update fails
        """
        start_time = datetime.utcnow()
        try:
            # Check if update needed
            if not self._should_update(environment):
                return
            
            # Get messages to process
            messages = self._get_messages(environment)
            if not messages:
                return
            
            # Process updates in batches
            batches = list(self._batch_messages(messages))
            
            if self.config.concurrent_updates:
                await self._process_batches_concurrent(batches, environment)
            else:
                await self._process_batches_sequential(batches, environment)
            
            # Update metrics
            if self.config.track_updates:
                duration = (datetime.utcnow() - start_time).total_seconds()
                self._update_metrics(messages, duration)
            
        except Exception as e:
            self.metrics.failed_updates += 1
            logger.error(f"Memory update failed: {str(e)}")
            raise ActionError(
                message=str(e),
                action=self.name,
                details={
                    "messages": len(messages),
                    "batches": len(batches),
                    "duration": (datetime.utcnow() - start_time).total_seconds()
                }
            )
    
    def _should_update(
        self,
        environment: BaseEnvironment
    ) -> bool:
        """Check if update should be performed
        
        Args:
            environment: Environment to check
            
        Returns:
            Whether update should be performed
        """
        return (
            environment.state.current_turn % self.config.update_interval == 0
        )
    
    def _get_messages(
        self,
        environment: BaseEnvironment
    ) -> List[Message]:
        """Get messages to process
        
        Args:
            environment: Environment to get messages from
            
        Returns:
            Messages to process
        """
        messages = environment.message_history
        
        if self.config.max_history:
            messages = messages[-self.config.max_history:]
        
        return messages
    
    def _batch_messages(
        self,
        messages: List[Message]
    ) -> List[List[Message]]:
        """Split messages into batches
        
        Args:
            messages: Messages to batch
            
        Returns:
            Batched messages
        """
        batches = []
        for i in range(0, len(messages), self.config.batch_size):
            batch = messages[i:i + self.config.batch_size]
            batches.append(batch)
            if self.config.track_updates:
                self.metrics.batch_sizes.append(len(batch))
        return batches
    
    async def _process_batches_concurrent(
        self,
        batches: List[List[Message]],
        environment: BaseEnvironment
    ) -> None:
        """Process batches concurrently
        
        Args:
            batches: Batches to process
            environment: Environment instance
        """
        async with asyncio.TaskGroup() as group:
            tasks = [
                group.create_task(
                    self._process_batch_with_retry(
                        batch,
                        environment
                    )
                )
                for batch in batches
            ]
    
    async def _process_batches_sequential(
        self,
        batches: List[List[Message]],
        environment: BaseEnvironment
    ) -> None:
        """Process batches sequentially
        
        Args:
            batches: Batches to process
            environment: Environment instance
        """
        for batch in batches:
            await self._process_batch_with_retry(batch, environment)
    
    async def _process_batch_with_retry(
        self,
        messages: List[Message],
        environment: BaseEnvironment
    ) -> None:
        """Process batch with retry logic
        
        Args:
            messages: Messages to process
            environment: Environment instance
        """
        retries = 0
        while retries < self.config.max_retries:
            try:
                async with asyncio.timeout(self.config.timeout_per_batch):
                    await self._process_batch(messages, environment)
                if self.config.track_updates:
                    self.metrics.retry_counts.append(retries)
                return
            except Exception as e:
                retries += 1
                if retries >= self.config.max_retries or not self.config.retry_failed:
                    raise
                logger.warning(
                    f"Batch processing failed (attempt {retries}): {str(e)}"
                )
                await asyncio.sleep(1)  # Brief delay before retry
    
    @abstractmethod
    async def _process_batch(
        self,
        messages: List[Message],
        environment: BaseEnvironment
    ) -> None:
        """Process a batch of messages
        
        Args:
            messages: Messages to process
            environment: Environment instance
        """
        pass
    
    def _update_metrics(
        self,
        messages: List[Message],
        duration: float
    ) -> None:
        """Update tracking metrics
        
        Args:
            messages: Processed messages
            duration: Update duration
        """
        self.metrics.total_updates += 1
        self.metrics.messages_processed += len(messages)
        self.metrics.last_update = datetime.utcnow()
        self.metrics.update_durations.append(duration)
        
        # Update agent stats
        for message in messages:
            if message.sender:
                stats = self.metrics.agent_stats.setdefault(
                    message.sender,
                    {"messages": 0, "updates": 0}
                )
                stats["messages"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get updater metrics
        
        Returns:
            Updater metrics
        """
        metrics = self.metrics.model_dump()
        
        # Add average metrics
        if self.metrics.update_durations:
            metrics["avg_duration"] = (
                sum(self.metrics.update_durations) /
                len(self.metrics.update_durations)
            )
        
        if self.metrics.batch_sizes:
            metrics["avg_batch_size"] = (
                sum(self.metrics.batch_sizes) /
                len(self.metrics.batch_sizes)
            )
        
        if self.metrics.retry_counts:
            metrics["avg_retries"] = (
                sum(self.metrics.retry_counts) /
                len(self.metrics.retry_counts)
            )
        
        return metrics
    
    def reset(self) -> None:
        """Reset updater state"""
        self.metrics = UpdateMetrics()
        logger.info(f"Reset {self.name} updater")

@updater_registry.register("basic")
class BasicUpdater(BaseUpdater):
    """Basic memory updater"""
    
    name: ClassVar[str] = "basic_updater"
    description: ClassVar[str] = "Basic memory updater implementation"
    version: ClassVar[str] = "1.1.0"
    
    async def _process_batch(
        self,
        messages: List[Message],
        environment: BaseEnvironment
    ) -> None:
        """Update agent memories with messages
        
        Args:
            messages: Messages to process
            environment: Environment instance
        """
        for agent in environment.agents:
            await agent.memory.add_messages(messages)

@updater_registry.register("selective")
class SelectiveUpdater(BaseUpdater):
    """Selective memory updater"""
    
    name: ClassVar[str] = "selective_updater"
    description: ClassVar[str] = "Selective memory updater implementation"
    version: ClassVar[str] = "1.1.0"
    
    async def _process_batch(
        self,
        messages: List[Message],
        environment: BaseEnvironment
    ) -> None:
        """Update agent memories with relevant messages
        
        Args:
            messages: Messages to process
            environment: Environment instance
        """
        for agent in environment.agents:
            # Filter messages relevant to this agent
            relevant = [
                msg for msg in messages
                if (
                    msg.sender == agent.name or
                    agent.name in msg.receiver or
                    "all" in msg.receiver
                )
            ]
            if relevant:
                await agent.memory.add_messages(relevant) 