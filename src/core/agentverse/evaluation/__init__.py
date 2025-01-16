"""
Evaluation Module

This module provides evaluation and metrics tracking for AgentVerse environments:

1. Evaluation Types:
   - Base: Core evaluation functionality
   - Performance: Speed and efficiency metrics
   - Quality: Output quality assessment
   - Resource: Resource utilization tracking
   - Behavior: Agent behavior analysis

2. Evaluation Features:
   - Metric collection
   - Performance tracking
   - Quality assessment
   - Resource monitoring
   - Behavior analysis

3. Evaluation Components:
   - Evaluators: Evaluation logic
   - Metrics: Measurement definitions
   - Registry: Evaluator management
   - Reports: Result formatting

Example Usage:
    ```python
    from src.core.agentverse.environment.evaluation import (
        BaseEvaluator,
        PerformanceMetrics,
        EvaluatorRegistry
    )

    # Create evaluator
    evaluator = BaseEvaluator(
        metrics=[
            PerformanceMetrics.LATENCY,
            PerformanceMetrics.THROUGHPUT,
            PerformanceMetrics.ERROR_RATE
        ]
    )

    # Register evaluator
    registry = EvaluatorRegistry()
    registry.register("perf_eval", evaluator)

    # Run evaluation
    async with evaluator:
        # Start collection
        await evaluator.start()
        
        # Record metrics
        await evaluator.record_metric(
            name="latency",
            value=125.5,
            tags={"operation": "task_execution"}
        )
        
        # Generate report
        report = await evaluator.generate_report()
    ```

Evaluation Process:
    ```
    Evaluation
    ├── Setup
    │   ├── Metrics
    │   ├── Thresholds
    │   └── Targets
    ├── Collection
    │   ├── Measurements
    │   ├── Events
    │   └── States
    ├── Analysis
    │   ├── Processing
    │   ├── Aggregation
    │   └── Comparison
    └── Reporting
        ├── Results
        ├── Insights
        └── Recommendations
    ```
"""

from src.core.agentverse.evaluation.base import (
    BaseEvaluator,
    EvaluatorConfig
)
from src.core.agentverse.evaluation.metrics import (
    BaseMetric,
    PerformanceMetrics,
    QualityMetrics,
    ResourceMetrics
)
from src.core.agentverse.evaluation.evaluators import (
    PerformanceEvaluator,
    QualityEvaluator,
    ResourceEvaluator
)
from src.core.agentverse.evaluation.registry import (
    EvaluatorRegistry,
    MetricRegistry
)

__all__ = [
    # Base
    'BaseEvaluator',
    'EvaluatorConfig',
    
    # Metrics
    'BaseMetric',
    'PerformanceMetrics',
    'QualityMetrics',
    'ResourceMetrics',
    
    # Evaluators
    'PerformanceEvaluator',
    'QualityEvaluator',
    'ResourceEvaluator',
    
    # Registry
    'EvaluatorRegistry',
    'MetricRegistry'
]

# Version
__version__ = "1.0.0" 