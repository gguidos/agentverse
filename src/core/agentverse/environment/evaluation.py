from typing import Dict, Any, List, Optional, Set, ClassVar
import asyncio
import logging
from datetime import datetime
from pydantic import Field, ConfigDict

from src.core.agentverse.environment.basic import BasicEnvironment, BasicEnvironmentState
from src.core.agentverse.environment.registry import env_registry
from src.core.agentverse.message.base import Message
from src.core.agentverse.environment.exceptions import EnvironmentError

logger = logging.getLogger(__name__)

class EvaluationMetrics(BaseModel):
    """Evaluation metrics configuration"""
    metrics: List[str] = [
        "relevance", "consistency", "fluency", "coherence"
    ]
    weights: Dict[str, float] = Field(default_factory=lambda: {
        "relevance": 0.3,
        "consistency": 0.3,
        "fluency": 0.2,
        "coherence": 0.2
    })
    thresholds: Dict[str, float] = Field(default_factory=lambda: {
        "relevance": 0.7,
        "consistency": 0.7,
        "fluency": 0.6,
        "coherence": 0.6
    })

class EvaluationState(BasicEnvironmentState):
    """State model for evaluation environment"""
    
    # Evaluation tracking
    evaluations_completed: int = 0
    evaluation_history: List[Dict[str, Any]] = Field(default_factory=list)
    current_scores: Dict[str, float] = Field(default_factory=dict)
    
    # Confidence tracking
    confidence_scores: List[float] = Field(default_factory=list)
    min_confidence: float = 0.7
    
    # Performance tracking
    evaluation_durations: List[float] = Field(default_factory=list)
    failed_evaluations: int = 0
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True
    )

@env_registry.register("llm_eval")
class EvaluationEnvironment(BasicEnvironment):
    """Environment for LLM-based evaluation tasks"""
    
    name: ClassVar[str] = "evaluation_environment"
    description: ClassVar[str] = "Environment for LLM-based evaluation and assessment"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        metrics_config: Optional[EvaluationMetrics] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.metrics_config = metrics_config or EvaluationMetrics()
        self.state = EvaluationState()
        
        # Initialize evaluation metrics
        self.state.metrics.update({
            "evaluations_completed": 0,
            "average_scores": {m: 0.0 for m in self.metrics_config.metrics},
            "confidence_scores": [],
            "failed_evaluations": 0
        })
        
        logger.info(
            f"Initialized evaluation environment with metrics: "
            f"{self.metrics_config.metrics}"
        )
    
    async def step(self) -> Dict[str, Any]:
        """Execute one evaluation step"""
        try:
            # Validate state
            if not await self.validate_state():
                raise EnvironmentError("Invalid evaluation state")
            
            # Update state
            self.state.status = "evaluating"
            step_start = datetime.utcnow()
            
            # Get active evaluators
            evaluators = await self._get_next_agents()
            if not evaluators:
                raise EnvironmentError("No evaluators available")
            
            # Get evaluation contexts
            contexts = await self._get_descriptions(evaluators)
            
            # Run evaluations concurrently
            async with asyncio.TaskGroup() as group:
                evaluation_tasks = [
                    group.create_task(
                        self._run_evaluation(
                            agent_id=agent_id,
                            context=contexts[agent_id]
                        )
                    )
                    for agent_id in evaluators
                ]
            
            evaluations = [task.result() for task in evaluation_tasks]
            
            # Process evaluation results
            processed_results = await self._process_evaluations(evaluations)
            
            # Create messages from evaluations
            messages = await self._create_evaluation_messages(processed_results)
            
            # Update state
            await self._update_after_evaluations(processed_results, messages)
            
            # Calculate step duration
            duration = (datetime.utcnow() - step_start).total_seconds()
            self._update_evaluation_metrics(duration, processed_results)
            
            return {
                "messages": messages,
                "evaluations": processed_results,
                "state": self.state.dict(),
                "is_done": await self.is_done(),
                "metrics": self.state.metrics
            }
            
        except Exception as e:
            self.state.status = "error"
            self.state.failed_evaluations += 1
            logger.error(f"Evaluation step failed: {str(e)}")
            raise EnvironmentError(f"Evaluation failed: {str(e)}")
    
    async def _run_evaluation(
        self,
        agent_id: str,
        context: str
    ) -> Dict[str, Any]:
        """Run single evaluation
        
        Args:
            agent_id: Evaluator ID
            context: Evaluation context
            
        Returns:
            Dict containing evaluation results
            
        Raises:
            EnvironmentError: If evaluation fails
        """
        try:
            async with self._locks[agent_id]:
                result = await self.rule.evaluate(
                    agent_id=agent_id,
                    context=context,
                    metrics=self.metrics_config.metrics,
                    state=self.state
                )
                return result
                
        except Exception as e:
            logger.error(f"Evaluator {agent_id} failed: {str(e)}")
            raise EnvironmentError(f"Evaluation failed: {str(e)}")
    
    async def _process_evaluations(
        self,
        evaluations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process and validate evaluation results
        
        Args:
            evaluations: Raw evaluation results
            
        Returns:
            List of processed evaluation results
        """
        processed = []
        
        for eval in evaluations:
            # Validate scores
            scores = eval.get("scores", {})
            for metric in self.metrics_config.metrics:
                if metric not in scores:
                    logger.warning(f"Missing metric: {metric}")
                    scores[metric] = 0.0
                elif not 0 <= scores[metric] <= 1:
                    logger.warning(f"Invalid score for {metric}: {scores[metric]}")
                    scores[metric] = max(0.0, min(1.0, scores[metric]))
            
            # Calculate weighted score
            weighted_score = sum(
                scores.get(m, 0) * self.metrics_config.weights.get(m, 1)
                for m in self.metrics_config.metrics
            )
            
            # Validate confidence
            confidence = eval.get("confidence", 0)
            if not 0 <= confidence <= 1:
                confidence = max(0.0, min(1.0, confidence))
            
            processed.append({
                "content": eval.get("content", ""),
                "scores": scores,
                "weighted_score": weighted_score,
                "confidence": confidence,
                "metadata": eval.get("metadata", {}),
                "passed_threshold": all(
                    scores.get(m, 0) >= self.metrics_config.thresholds.get(m, 0)
                    for m in self.metrics_config.metrics
                )
            })
        
        return processed
    
    async def _create_evaluation_messages(
        self,
        evaluations: List[Dict[str, Any]]
    ) -> List[Message]:
        """Create messages from evaluation results"""
        messages = []
        
        for i, eval in enumerate(evaluations):
            message = Message(
                content=eval["content"],
                sender=f"evaluator_{i}",
                receiver={"all"},
                metadata={
                    "scores": eval["scores"],
                    "weighted_score": eval["weighted_score"],
                    "confidence": eval["confidence"],
                    "passed_threshold": eval["passed_threshold"],
                    "is_final": await self.is_done()
                }
            )
            messages.append(message)
        
        return messages
    
    async def _update_after_evaluations(
        self,
        evaluations: List[Dict[str, Any]],
        messages: List[Message]
    ) -> None:
        """Update state after evaluations"""
        # Update evaluation history
        self.state.evaluation_history.extend(evaluations)
        
        # Update message history
        self.state.last_messages = messages
        self.state.message_history.extend(messages)
        
        # Update current scores
        for metric in self.metrics_config.metrics:
            scores = [eval["scores"].get(metric, 0) for eval in evaluations]
            self.state.current_scores[metric] = sum(scores) / len(scores) if scores else 0
        
        # Update confidence scores
        confidences = [eval["confidence"] for eval in evaluations]
        if confidences:
            self.state.confidence_scores.append(
                sum(confidences) / len(confidences)
            )
        
        # Update counters
        self.state.evaluations_completed += len(evaluations)
        self.state.current_turn += 1
        
        # Update status
        self.state.status = "completed"
        self.state.last_update = datetime.utcnow()
    
    def _update_evaluation_metrics(
        self,
        duration: float,
        evaluations: List[Dict[str, Any]]
    ) -> None:
        """Update metrics after evaluations"""
        metrics = self.state.metrics
        
        # Update counts
        metrics["total_evaluations"] = self.state.evaluations_completed
        metrics["failed_evaluations"] = self.state.failed_evaluations
        
        # Update scores
        for metric in self.metrics_config.metrics:
            scores = [eval["scores"].get(metric, 0) for eval in evaluations]
            if scores:
                metrics["average_scores"][metric] = (
                    metrics["average_scores"][metric] * 
                    (metrics["total_evaluations"] - len(evaluations)) +
                    sum(scores)
                ) / metrics["total_evaluations"]
        
        # Update confidence
        confidences = [eval["confidence"] for eval in evaluations]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            metrics["confidence_scores"].append(avg_confidence)
        
        # Update duration
        self.state.evaluation_durations.append(duration)
        metrics["avg_evaluation_duration"] = (
            sum(self.state.evaluation_durations) / 
            len(self.state.evaluation_durations)
        ) 