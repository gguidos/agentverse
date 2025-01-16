from typing import List, Dict, Any, Optional, ClassVar
import logging
from datetime import datetime

from src.core.agentverse.environment.updaters.base import (
    BaseUpdater,
    UpdaterConfig,
    UpdateMetrics
)
from src.core.agentverse.environment.registry import updater_registry
from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.message.base import Message
from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.environment.exceptions import ActionError

logger = logging.getLogger(__name__)

class BasicUpdaterConfig(UpdaterConfig):
    """Configuration for basic updater"""
    handle_silence: bool = True
    silence_message: str = "[Silence]"
    track_tool_responses: bool = True
    tool_response_timeout: float = 5.0
    max_tool_retries: int = 2
    broadcast_tool_responses: bool = False
    
    model_config = ConfigDict(
        extra="allow"
    )

class BasicUpdaterMetrics(UpdateMetrics):
    """Additional metrics for basic updater"""
    tool_responses_processed: int = 0
    silence_messages_sent: int = 0
    failed_tool_updates: int = 0
    tool_response_times: List[float] = Field(default_factory=list)

@updater_registry.register("basic")
class BasicUpdater(BaseUpdater):
    """Basic memory updater with tool response handling"""
    
    name: ClassVar[str] = "basic_updater"
    description: ClassVar[str] = "Basic updater with tool response handling"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        config: Optional[BasicUpdaterConfig] = None
    ):
        super().__init__(config=config or BasicUpdaterConfig())
        self.basic_metrics = BasicUpdaterMetrics()
    
    async def _process_batch(
        self,
        messages: List[Message],
        environment: BaseEnvironment
    ) -> None:
        """Process messages and tool responses
        
        Args:
            messages: Messages to process
            environment: Environment instance
            
        Raises:
            ActionError: If processing fails
        """
        try:
            messages_added = False
            start_time = datetime.utcnow()
            
            for message in messages:
                # Handle tool responses
                if message.tool_response:
                    await self._handle_tool_responses(
                        message=message,
                        environment=environment
                    )
                
                # Skip empty messages
                if not message.content:
                    continue
                
                # Add message to appropriate agents
                added = await self._distribute_message(
                    message=message,
                    environment=environment
                )
                messages_added = messages_added or added
            
            # Handle silence if needed
            if not messages_added and self.config.handle_silence:
                await self._handle_silence(environment)
            
            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._update_basic_metrics(messages, duration)
            
        except Exception as e:
            logger.error(f"Message processing failed: {str(e)}")
            raise ActionError(
                message=str(e),
                action=self.name,
                details={
                    "messages": len(messages),
                    "environment": environment.name
                }
            )
    
    async def _handle_tool_responses(
        self,
        message: Message,
        environment: BaseEnvironment
    ) -> None:
        """Handle tool responses
        
        Args:
            message: Message with tool responses
            environment: Environment instance
        """
        start_time = datetime.utcnow()
        retries = 0
        
        try:
            while retries < self.config.max_tool_retries:
                try:
                    # Get target agent
                    agent = environment.get_agent_by_name(message.sender)
                    if not agent or not hasattr(agent, 'tool_memory'):
                        if self.config.broadcast_tool_responses:
                            # Broadcast to all agents with tool memory
                            for agent in environment.agents:
                                if hasattr(agent, 'tool_memory'):
                                    await agent.tool_memory.add_messages(
                                        message.tool_response
                                    )
                        return
                    
                    # Add to agent's tool memory
                    await agent.tool_memory.add_messages(message.tool_response)
                    
                    # Update metrics
                    duration = (
                        datetime.utcnow() - start_time
                    ).total_seconds()
                    self.basic_metrics.tool_responses_processed += 1
                    self.basic_metrics.tool_response_times.append(duration)
                    return
                    
                except Exception as e:
                    retries += 1
                    if retries >= self.config.max_tool_retries:
                        raise
                    logger.warning(
                        f"Tool response update failed (attempt {retries}): {str(e)}"
                    )
                    await asyncio.sleep(1)
            
        except Exception as e:
            self.basic_metrics.failed_tool_updates += 1
            logger.error(f"Tool response handling failed: {str(e)}")
            raise ActionError(
                message=str(e),
                action=f"{self.name}_tool_response",
                details={
                    "sender": message.sender,
                    "responses": len(message.tool_response)
                }
            )
    
    async def _distribute_message(
        self,
        message: Message,
        environment: BaseEnvironment
    ) -> bool:
        """Distribute message to appropriate agents
        
        Args:
            message: Message to distribute
            environment: Environment instance
            
        Returns:
            Whether message was distributed
        """
        try:
            if "all" in message.receiver:
                # Broadcast to all agents
                for agent in environment.agents:
                    await agent.memory.add_messages([message])
                return True
            
            else:
                # Send to specific agents
                receiver_set = set(message.receiver)
                for agent in environment.agents:
                    if agent.name in receiver_set:
                        await agent.memory.add_messages([message])
                        receiver_set.remove(agent.name)
                
                # Check for missing receivers
                if receiver_set:
                    missing = ", ".join(receiver_set)
                    raise ValueError(f"Receivers not found: {missing}")
                
                return True
            
        except Exception as e:
            logger.error(f"Message distribution failed: {str(e)}")
            return False
    
    async def _handle_silence(
        self,
        environment: BaseEnvironment
    ) -> None:
        """Add silence message when no one speaks
        
        Args:
            environment: Environment instance
        """
        try:
            silence_msg = Message(
                content=self.config.silence_message,
                sender="system",
                receiver=["all"],
                timestamp=datetime.utcnow()
            )
            
            for agent in environment.agents:
                await agent.memory.add_messages([silence_msg])
            
            self.basic_metrics.silence_messages_sent += 1
            
        except Exception as e:
            logger.error(f"Silence handling failed: {str(e)}")
    
    def _update_basic_metrics(
        self,
        messages: List[Message],
        duration: float
    ) -> None:
        """Update basic updater metrics
        
        Args:
            messages: Processed messages
            duration: Processing duration
        """
        super()._update_metrics(messages, duration)
        
        # Update tool response metrics
        tool_responses = sum(
            1 for m in messages
            if m.tool_response
        )
        self.basic_metrics.tool_responses_processed += tool_responses
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics including basic metrics
        
        Returns:
            Combined metrics
        """
        metrics = super().get_metrics()
        basic_metrics = self.basic_metrics.model_dump()
        
        # Add average tool response time
        if self.basic_metrics.tool_response_times:
            basic_metrics["avg_tool_response_time"] = (
                sum(self.basic_metrics.tool_response_times) /
                len(self.basic_metrics.tool_response_times)
            )
        
        metrics.update(basic_metrics)
        return metrics
    
    def reset(self) -> None:
        """Reset updater state"""
        super().reset()
        self.basic_metrics = BasicUpdaterMetrics() 