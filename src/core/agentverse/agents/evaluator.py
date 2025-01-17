"""Evaluator agent implementation"""

from typing import Dict, Any, Optional, List, Union
import logging
import asyncio
from pydantic import BaseModel, Field

from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.agents.config import AgentConfig
from src.core.agentverse.agents.mixins.message_handler import MessageHandlerMixin
from src.core.agentverse.agents.mixins.memory_handler import MemoryHandlerMixin
from src.core.agentverse.message import Message, MessageType
from src.core.agentverse.memory import BaseMemory
from src.core.agentverse.services.llm import BaseLLMService
from src.core.agentverse.message_bus import BaseMessageBus
from src.core.agentverse.registry import agent_registry

logger = logging.getLogger(__name__)

class EvaluationMetrics(BaseModel):
    """Evaluation metrics"""
    accuracy: float = 0.0
    relevance: float = 0.0
    coherence: float = 0.0
    helpfulness: float = 0.0
    safety: float = 0.0
    
    def average(self) -> float:
        """Calculate average score"""
        return sum([
            self.accuracy,
            self.relevance,
            self.coherence,
            self.helpfulness,
            self.safety
        ]) / 5.0

class EvaluationResult(BaseModel):
    """Evaluation result"""
    id: str
    agent_id: str
    message_id: str
    metrics: EvaluationMetrics
    feedback: str
    timestamp: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EvaluatorConfig(AgentConfig):
    """Evaluator configuration"""
    evaluation_interval: float = 1.0
    batch_size: int = 10
    min_context: int = 3
    metrics_threshold: float = 0.7
    distributed: bool = False
    llm_config: Dict[str, Any] = Field(default_factory=dict)

@agent_registry.register("evaluator")
class EvaluatorAgent(BaseAgent, MessageHandlerMixin, MemoryHandlerMixin):
    """Enhanced evaluator agent"""
    
    def __init__(
        self,
        config: EvaluatorConfig,
        message_bus: Optional[BaseMessageBus] = None,
        memory: Optional[BaseMemory] = None,
        llm: Optional[BaseLLMService] = None
    ):
        """Initialize evaluator
        
        Args:
            config: Evaluator configuration
            message_bus: Optional message bus
            memory: Optional memory backend
            llm: Optional LLM service
        """
        BaseAgent.__init__(self, name=config.name, llm=llm)
        MessageHandlerMixin.__init__(self)
        MemoryHandlerMixin.__init__(self, memory)
        
        self.config = config
        self.message_bus = message_bus
        
        # Register handlers
        self.register_handler(MessageType.CHAT, self.handle_chat)
        self.register_handler(MessageType.COMMAND, self.handle_command)
        self.register_handler(MessageType.EVENT, self.handle_event)
    
    async def handle_chat(self, message: Message) -> None:
        """Handle chat message
        
        Args:
            message: Chat message to evaluate
        """
        try:
            # Store message
            await self.remember(message)
            
            # Get context
            context = await self.get_context(
                filter_dict={
                    "conversation_id": message.metadata.get("conversation_id")
                }
            )
            
            # Evaluate message
            evaluation = await self._evaluate_message(message, context)
            
            # Create response
            response = Message(
                content=evaluation.feedback,
                type=MessageType.CHAT,
                sender=self.name,
                receiver={"all"},
                metadata={
                    "conversation_id": message.metadata.get("conversation_id"),
                    "parent_id": message.id,
                    "metrics": evaluation.metrics.dict(),
                    "evaluation_id": evaluation.id
                }
            )
            
            # Store and send response
            await self.remember(response)
            await self.send_message(response)
            
        except Exception as e:
            logger.error(f"Chat handling failed: {str(e)}")
    
    async def handle_event(self, message: Message) -> None:
        """Handle evaluation events
        
        Args:
            message: Event message
        """
        if message.type != MessageType.EVENT:
            return
            
        event_type = message.metadata.get("event_type")
        
        if event_type == "evaluation_requested":
            await self.evaluate_agent(message.metadata.get("agent_id"))
            
        elif event_type == "metrics_updated":
            await self.update_metrics(message.metadata.get("data"))
    
    async def evaluate_batch(self) -> None:
        """Evaluate batch of messages"""
        try:
            messages = self._eval_queue[:self.config.batch_size]
            self._eval_queue = self._eval_queue[self.config.batch_size:]
            
            # Get context for messages
            contexts = {}
            for msg in messages:
                context = await self.get_context(
                    filter_dict={
                        "conversation_id": msg["metadata"]["conversation_id"]
                    },
                    k=self.config.min_context
                )
                contexts[msg["id"]] = context
            
            # Evaluate messages
            results = []
            for msg in messages:
                result = await self.evaluate_message(
                    msg,
                    context=contexts[msg["id"]]
                )
                results.append(result)
            
            # Store results
            for result in results:
                await self.remember(result.dict())
            
            # Publish evaluation event
            await self.send_message(
                EventMessage(
                    event_type="evaluation_completed",
                    data={
                        "results": [r.dict() for r in results]
                    }
                )
            )
            
        except Exception as e:
            logger.error(f"Batch evaluation failed: {str(e)}")
    
    async def evaluate_message(
        self,
        message: Dict[str, Any],
        context: Optional[List[Dict[str, Any]]] = None
    ) -> EvaluationResult:
        """Evaluate single message
        
        Args:
            message: Message to evaluate
            context: Optional conversation context
            
        Returns:
            Evaluation result
        """
        try:
            # Evaluate metrics
            metrics = await self._evaluate_metrics(message, context)
            
            # Generate feedback
            feedback = await self._generate_feedback(message, metrics, context)
            
            # Create result
            result = EvaluationResult(
                id=str(uuid.uuid4()),
                agent_id=message["metadata"]["source"],
                message_id=message["id"],
                metrics=metrics,
                feedback=feedback,
                timestamp=time.time()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Message evaluation failed: {str(e)}")
            raise
    
    async def _evaluate_metrics(
        self,
        message: Dict[str, Any],
        context: Optional[List[Dict[str, Any]]] = None
    ) -> EvaluationMetrics:
        """Evaluate message metrics
        
        Args:
            message: Message to evaluate
            context: Optional conversation context
            
        Returns:
            Evaluation metrics
        """
        if not self.llm:
            return EvaluationMetrics()
        
        try:
            # Build input from context and message
            input_text = self._build_context_text(context) if context else ""
            message_text = message["content"]
            
            # Get evaluation scores
            scores = await self.llm.evaluate(
                input=input_text,
                output=message_text
            )
            
            return EvaluationMetrics(**scores)
            
        except Exception as e:
            logger.error(f"Metric evaluation failed: {str(e)}")
            return EvaluationMetrics()
    
    async def _generate_feedback(
        self,
        message: Dict[str, Any],
        metrics: EvaluationMetrics,
        context: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Generate evaluation feedback
        
        Args:
            message: Evaluated message
            metrics: Evaluation metrics
            context: Optional conversation context
            
        Returns:
            Feedback text
        """
        if not self.llm:
            return ""
        
        try:
            # Build feedback prompt
            prompt = self._build_feedback_prompt(message, metrics, context)
            
            # Generate feedback
            response = await self.llm.generate(prompt)
            
            return response.text
            
        except Exception as e:
            logger.error(f"Feedback generation failed: {str(e)}")
            return ""
    
    async def process(self) -> None:
        """Process evaluation queue"""
        while self._running:
            try:
                # Process queued evaluations
                if self._eval_queue:
                    await self.evaluate_batch()
                
                # Wait for interval
                await asyncio.sleep(self.config.evaluation_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Evaluation processing failed: {str(e)}")
                await asyncio.sleep(1) 