from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict

from src.core.agentverse.evaluation.base import (
    BaseEvaluator,
    EvaluationResult,
    EvaluationMetric,
    EvaluatorConfig
)
from src.core.agentverse.evaluation.registry import evaluator_registry

logger = logging.getLogger(__name__)

class AgentEvaluatorConfig(EvaluatorConfig):
    """Configuration for agent evaluators"""
    response_time_threshold: float = 5.0  # seconds
    memory_usage_threshold: int = 100 * 1024 * 1024  # 100MB
    min_response_length: int = 10
    max_response_length: int = 1000
    track_token_usage: bool = True

@evaluator_registry.register("agent_performance")
class AgentPerformanceEvaluator(BaseEvaluator):
    """Evaluator for agent performance metrics"""
    
    name: str = "agent_performance"
    description: str = "Evaluates agent performance including response time, quality, and resource usage"
    version: str = "1.1.0"
    
    def __init__(self, config: Optional[AgentEvaluatorConfig] = None):
        super().__init__(config=config or AgentEvaluatorConfig())
        self.response_times: List[float] = []
        self.memory_usage: List[int] = []
        self.token_counts: List[int] = []
    
    async def evaluate(self, data: Dict[str, Any]) -> EvaluationResult:
        """Evaluate agent performance
        
        Args:
            data: Dictionary containing:
                - response_time: Time taken to generate response
                - response_text: Generated response
                - memory_usage: Memory used during generation
                - token_count: Number of tokens used
                - error_count: Number of errors encountered
                - success: Whether the operation was successful
        """
        try:
            # Extract metrics
            response_time = data.get("response_time", 0.0)
            response_text = data.get("response_text", "")
            memory_usage = data.get("memory_usage", 0)
            token_count = data.get("token_count", 0)
            error_count = data.get("error_count", 0)
            success = data.get("success", False)
            
            # Store raw data if enabled
            self.store_raw_data(data)
            
            # Update historical data
            self.response_times.append(response_time)
            self.memory_usage.append(memory_usage)
            self.token_counts.append(token_count)
            
            # Calculate metrics
            metrics = [
                # Response time metrics
                EvaluationMetric(
                    name="response_time",
                    value=response_time,
                    description="Time taken to generate response (seconds)",
                    metadata={"threshold": self.config.response_time_threshold}
                ),
                
                # Memory usage metrics
                EvaluationMetric(
                    name="memory_usage",
                    value=memory_usage / (1024 * 1024),  # Convert to MB
                    description="Memory used during generation (MB)",
                    metadata={"threshold": self.config.memory_usage_threshold}
                ),
                
                # Response quality metrics
                EvaluationMetric(
                    name="response_length",
                    value=len(response_text),
                    description="Length of generated response",
                    metadata={
                        "min_length": self.config.min_response_length,
                        "max_length": self.config.max_response_length
                    }
                ),
                
                # Error metrics
                EvaluationMetric(
                    name="error_rate",
                    value=error_count,
                    description="Number of errors encountered",
                    metadata={"total_operations": 1}
                )
            ]
            
            # Add token usage metrics if enabled
            if self.config.track_token_usage:
                metrics.append(
                    EvaluationMetric(
                        name="token_usage",
                        value=token_count,
                        description="Number of tokens used",
                        metadata={"total_tokens": sum(self.token_counts)}
                    )
                )
            
            # Calculate overall score
            score = self._calculate_score(metrics)
            
            # Create result
            result = EvaluationResult(
                success=success,
                score=score,
                metrics=metrics,
                feedback=self._generate_feedback(metrics, score),
                metadata={
                    "timestamp": datetime.utcnow(),
                    "avg_response_time": np.mean(self.response_times[-100:]),
                    "avg_memory_usage": np.mean(self.memory_usage[-100:]),
                    "total_evaluations": len(self.response_times)
                }
            )
            
            # Store result
            self.add_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Evaluation error: {str(e)}")
            return EvaluationResult(
                success=False,
                score=0.0,
                metrics=[],
                feedback=f"Evaluation failed: {str(e)}"
            )
    
    def _calculate_score(self, metrics: List[EvaluationMetric]) -> float:
        """Calculate overall performance score"""
        scores = {
            "response_time": 0.0,
            "memory_usage": 0.0,
            "response_length": 0.0,
            "error_rate": 0.0
        }
        
        for metric in metrics:
            if metric.name == "response_time":
                scores["response_time"] = max(
                    0.0,
                    1.0 - (metric.value / self.config.response_time_threshold)
                )
            elif metric.name == "memory_usage":
                scores["memory_usage"] = max(
                    0.0,
                    1.0 - (metric.value / (self.config.memory_usage_threshold / (1024 * 1024)))
                )
            elif metric.name == "response_length":
                length_score = 1.0
                if metric.value < self.config.min_response_length:
                    length_score = metric.value / self.config.min_response_length
                elif metric.value > self.config.max_response_length:
                    length_score = self.config.max_response_length / metric.value
                scores["response_length"] = length_score
            elif metric.name == "error_rate":
                scores["error_rate"] = 1.0 if metric.value == 0 else 0.0
        
        # Weight and combine scores
        weights = {
            "response_time": 0.3,
            "memory_usage": 0.2,
            "response_length": 0.2,
            "error_rate": 0.3
        }
        
        return sum(score * weights[name] for name, score in scores.items())
    
    def _generate_feedback(self, metrics: List[EvaluationMetric], score: float) -> str:
        """Generate human-readable feedback"""
        feedback = []
        
        # Overall performance
        if score >= 0.8:
            feedback.append("Excellent performance overall.")
        elif score >= 0.6:
            feedback.append("Good performance with some room for improvement.")
        else:
            feedback.append("Performance needs improvement.")
        
        # Specific metrics
        for metric in metrics:
            if metric.name == "response_time" and metric.value > self.config.response_time_threshold:
                feedback.append(f"Response time ({metric.value:.2f}s) exceeds threshold.")
            elif metric.name == "memory_usage" and metric.value > self.config.memory_usage_threshold:
                feedback.append(f"High memory usage ({metric.value:.2f}MB).")
            elif metric.name == "error_rate" and metric.value > 0:
                feedback.append(f"Encountered {metric.value} errors.")
        
        return " ".join(feedback) 