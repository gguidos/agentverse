from typing import List, Dict, Any, Optional, ClassVar
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging

from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.agents.actions import AgentAction, AgentStep, ActionSequence
from src.core.agentverse.message.base import Message
from src.core.agentverse.memory.base import BaseMemory
from src.core.agentverse.services.llm.base import BaseLLMService
from src.core.agentverse.registry import agent_registry
from src.core.agentverse.exceptions import AgentError

logger = logging.getLogger(__name__)

class ConversationConfig(BaseModel):
    """Configuration for conversation agent"""
    max_retries: int = 3
    history_limit: int = 10
    temperature: float = 0.7
    validate_responses: bool = True
    track_tokens: bool = True
    cache_responses: bool = True
    
    model_config = ConfigDict(
        extra="allow"
    )

class ConversationState(BaseModel):
    """State for conversation agent"""
    total_messages: int = 0
    total_tokens: int = 0
    last_message: Optional[datetime] = None
    error_count: int = 0
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

@agent_registry.register("conversation")
class ConversationAgent(BaseAgent):
    """Agent for handling conversations"""
    
    name: ClassVar[str] = "conversation"
    description: ClassVar[str] = "Conversation handling agent"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        llm_service: BaseLLMService,
        memory: BaseMemory,
        config: Optional[ConversationConfig] = None
    ):
        """Initialize conversation agent
        
        Args:
            llm_service: LLM service instance
            memory: Memory instance
            config: Optional configuration
        """
        super().__init__(
            llm_service=llm_service,
            memory=memory,
            config=config or ConversationConfig()
        )
        self.state = ConversationState()
        self.action_sequence = ActionSequence()
        logger.info(f"Initialized {self.name} v{self.version}")
    
    async def process_message(
        self,
        message: Message
    ) -> Message:
        """Process incoming message
        
        Args:
            message: Input message
            
        Returns:
            Response message
            
        Raises:
            AgentError: If processing fails
        """
        try:
            start_time = datetime.utcnow()
            
            # Create conversation action
            action = AgentAction(
                tool="converse",
                input={
                    "message": message.content,
                    "sender": message.sender
                }
            )
            step = AgentStep(action=action)
            
            try:
                # Get response
                response = await self._generate_with_retry(message)
                
                # Update action/step
                action.complete(
                    output=response.dict(),
                    duration=step.duration
                )
                step.complete(response.dict())
                
            except Exception as e:
                action.fail(str(e))
                step.fail(str(e))
                logger.error(f"Message processing failed: {str(e)}")
            
            # Track step
            self.action_sequence.add_step(step)
            
            # Update state
            self.state.total_messages += 1
            self.state.last_message = datetime.utcnow()
            if hasattr(response, 'usage'):
                self.state.total_tokens += response.usage.total_tokens
            
            # Create response message
            response_msg = Message(
                content=response.choices[0].message.content,
                sender=self.name,
                receiver={message.sender} if message.sender else {"all"},
                metadata={
                    "duration": step.duration,
                    "tokens": response.usage.total_tokens if hasattr(response, 'usage') else None,
                    "temperature": self.config.temperature
                }
            )
            
            # Store in memory if configured
            if self.config.cache_responses:
                await self.memory.add(
                    content=response_msg.content,
                    metadata={
                        "sender": self.name,
                        "receiver": response_msg.receiver,
                        "timestamp": datetime.utcnow()
                    }
                )
            
            return response_msg
            
        except Exception as e:
            self.state.error_count += 1
            logger.error(f"Message processing failed: {str(e)}")
            raise AgentError(
                message=f"Failed to process message: {str(e)}",
                details={
                    "sender": message.sender,
                    "content_length": len(message.content)
                }
            )
    
    async def _generate_with_retry(
        self,
        message: Message,
        attempt: int = 0
    ) -> Any:
        """Generate response with retry logic
        
        Args:
            message: Input message
            attempt: Current attempt number
            
        Returns:
            LLM response
            
        Raises:
            AgentError: If generation fails
        """
        try:
            # Get conversation history
            history = await self.memory.get_messages(
                limit=self.config.history_limit
            )
            
            # Build messages
            messages = [
                {
                    "role": "system",
                    "content": self.config.system_prompt
                }
            ]
            
            # Add history
            if history:
                messages.extend([
                    msg.to_dict() for msg in history
                ])
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message.content
            })
            
            # Get response
            response = await self.llm.chat_completion(
                messages=messages,
                temperature=self.config.temperature
            )
            
            return response
            
        except Exception as e:
            if attempt < self.config.max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                return await self._generate_with_retry(
                    message,
                    attempt + 1
                )
            else:
                logger.error(f"All retry attempts failed: {str(e)}")
                raise AgentError(
                    message=f"Failed to generate response: {str(e)}",
                    details={"attempts": attempt + 1}
                )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics
        
        Returns:
            Metrics dictionary
        """
        metrics = super().get_metrics()
        
        # Add conversation metrics
        metrics.update({
            "total_messages": self.state.total_messages,
            "total_tokens": self.state.total_tokens,
            "error_rate": (
                self.state.error_count / self.state.total_messages
                if self.state.total_messages > 0 else 0
            ),
            "avg_tokens_per_message": (
                self.state.total_tokens / self.state.total_messages
                if self.state.total_messages > 0 else 0
            )
        })
        
        # Add sequence metrics
        if self.action_sequence:
            metrics.update(self.action_sequence.get_metrics())
            
        return metrics
    
    async def reset(self) -> None:
        """Reset agent state"""
        await super().reset()
        self.state = ConversationState()
        self.action_sequence = ActionSequence() 