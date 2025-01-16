from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, ClassVar
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class EvaluationMetric(BaseModel):
    """Base model for evaluation metrics"""
    name: str
    value: float
    description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EvaluationResult(BaseModel):
    """Model for evaluation results"""
    success: bool
    score: float
    metrics: List[EvaluationMetric]
    feedback: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }

class EvaluatorConfig(BaseModel):
    """Configuration for evaluators"""
    metrics_history_size: int = 1000
    min_score_threshold: float = 0.0
    max_score_threshold: float = 1.0
    store_raw_data: bool = False
    cache_results: bool = True
    
    model_config = {
        "extra": "allow"
    }

class BaseEvaluator(ABC):
    """Base class for evaluators"""
    
    name: ClassVar[str] = "base_evaluator"
    description: ClassVar[str] = "Base evaluator class"
    version: ClassVar[str] = "1.0.0"
    
    def __init__(self, config: Optional[EvaluatorConfig] = None):
        """Initialize evaluator
        
        Args:
            config: Optional evaluator configuration
        """
        self.config = config or EvaluatorConfig()
        self._metrics_history: List[EvaluationMetric] = []
        self._results_history: List[EvaluationResult] = []
        self._raw_data: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized {self.name} evaluator v{self.version}")
    
    @abstractmethod
    async def evaluate(self, data: Dict[str, Any]) -> EvaluationResult:
        """Evaluate data and return results
        
        Args:
            data: Data to evaluate
            
        Returns:
            EvaluationResult: Evaluation results
        """
        pass
    
    async def get_metrics(self) -> Dict[str, List[EvaluationMetric]]:
        """Get evaluation metrics history
        
        Returns:
            Dict mapping metric names to their history
        """
        metrics_by_name: Dict[str, List[EvaluationMetric]] = {}
        
        for metric in self._metrics_history:
            if metric.name not in metrics_by_name:
                metrics_by_name[metric.name] = []
            metrics_by_name[metric.name].append(metric)
        
        return metrics_by_name
    
    async def get_average_metrics(self) -> Dict[str, float]:
        """Get average values for each metric
        
        Returns:
            Dict mapping metric names to average values
        """
        metrics = await self.get_metrics()
        return {
            name: sum(m.value for m in history) / len(history)
            for name, history in metrics.items()
            if history
        }
    
    def add_metric(self, metric: EvaluationMetric) -> None:
        """Add a metric to history
        
        Args:
            metric: Metric to add
        """
        self._metrics_history.append(metric)
        
        # Maintain history size limit
        while len(self._metrics_history) > self.config.metrics_history_size:
            self._metrics_history.pop(0)
    
    def add_result(self, result: EvaluationResult) -> None:
        """Add an evaluation result to history
        
        Args:
            result: Result to add
        """
        self._results_history.append(result)
        
        # Add metrics to history
        for metric in result.metrics:
            self.add_metric(metric)
        
        # Maintain history size limit
        while len(self._results_history) > self.config.metrics_history_size:
            self._results_history.pop(0)
    
    async def get_results_history(
        self,
        limit: Optional[int] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None
    ) -> List[EvaluationResult]:
        """Get filtered evaluation results history
        
        Args:
            limit: Maximum number of results to return
            min_score: Minimum score filter
            max_score: Maximum score filter
            
        Returns:
            List of evaluation results
        """
        results = self._results_history.copy()
        
        if min_score is not None:
            results = [r for r in results if r.score >= min_score]
        if max_score is not None:
            results = [r for r in results if r.score <= max_score]
        
        if limit:
            results = results[-limit:]
            
        return results
    
    def store_raw_data(self, data: Dict[str, Any]) -> None:
        """Store raw evaluation data if enabled
        
        Args:
            data: Raw data to store
        """
        if self.config.store_raw_data:
            self._raw_data.append({
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def export_metrics(self, format: str = "json") -> str:
        """Export metrics history in specified format
        
        Args:
            format: Export format (json/csv)
            
        Returns:
            Formatted metrics data
        """
        metrics = await self.get_metrics()
        
        if format == "json":
            return json.dumps({
                name: [m.dict() for m in history]
                for name, history in metrics.items()
            }, indent=2)
            
        elif format == "csv":
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(["metric", "value", "timestamp", "description"])
            
            # Write data
            for history in metrics.values():
                for metric in history:
                    writer.writerow([
                        metric.name,
                        metric.value,
                        metric.timestamp.isoformat(),
                        metric.description
                    ])
            
            return output.getvalue()
            
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def clear_history(self) -> None:
        """Clear all historical data"""
        self._metrics_history.clear()
        self._results_history.clear()
        self._raw_data.clear()
        logger.info(f"Cleared history for {self.name} evaluator") 