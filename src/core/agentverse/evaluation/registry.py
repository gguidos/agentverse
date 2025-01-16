from typing import Dict, Type, Any, Optional, List
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from src.core.agentverse.evaluation.base import BaseEvaluator, EvaluatorConfig

logger = logging.getLogger(__name__)

class EvaluatorRegistryConfig(BaseModel):
    """Configuration for evaluator registry"""
    allow_duplicates: bool = False
    validate_evaluators: bool = True
    track_usage: bool = True
    auto_initialize: bool = True

class EvaluatorInfo(BaseModel):
    """Information about registered evaluator"""
    name: str
    description: str
    version: str
    config_class: Optional[Type[EvaluatorConfig]] = None
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    usage_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EvaluatorRegistry(BaseModel):
    """Registry for evaluator types"""
    
    name: str = "EvaluatorRegistry"
    config: EvaluatorRegistryConfig = Field(default_factory=EvaluatorRegistryConfig)
    entries: Dict[str, Type[BaseEvaluator]] = Field(default_factory=dict)
    info: Dict[str, EvaluatorInfo] = Field(default_factory=dict)
    
    model_config = {
        "arbitrary_types_allowed": True
    }
    
    def register(self, key: str, **metadata):
        """Register an evaluator class
        
        Args:
            key: Registry key for the evaluator
            **metadata: Additional metadata for the evaluator
        """
        def decorator(evaluator_class: Type[BaseEvaluator]):
            # Validate evaluator class
            if not issubclass(evaluator_class, BaseEvaluator):
                raise ValueError(f"Class {evaluator_class.__name__} must inherit from BaseEvaluator")
            
            # Check for duplicates
            if key in self.entries and not self.config.allow_duplicates:
                raise KeyError(f"Evaluator '{key}' already registered")
            
            # Validate evaluator if enabled
            if self.config.validate_evaluators:
                try:
                    if self.config.auto_initialize:
                        evaluator = evaluator_class()
                        # Test basic functionality
                        assert hasattr(evaluator, 'evaluate'), "Missing evaluate method"
                        assert hasattr(evaluator, 'get_metrics'), "Missing get_metrics method"
                except Exception as e:
                    logger.error(f"Evaluator validation failed: {str(e)}")
                    raise ValueError(f"Invalid evaluator class: {str(e)}")
            
            # Register evaluator
            self.entries[key] = evaluator_class
            
            # Store evaluator info
            self.info[key] = EvaluatorInfo(
                name=getattr(evaluator_class, 'name', key),
                description=getattr(evaluator_class, 'description', ''),
                version=getattr(evaluator_class, 'version', '1.0.0'),
                config_class=getattr(evaluator_class, 'config_class', None),
                metadata=metadata
            )
            
            logger.info(f"Registered evaluator '{key}' ({evaluator_class.__name__})")
            return evaluator_class
            
        return decorator
    
    def get(
        self,
        key: str,
        config: Optional[EvaluatorConfig] = None,
        **kwargs
    ) -> BaseEvaluator:
        """Get an evaluator instance
        
        Args:
            key: Registry key for the evaluator
            config: Optional evaluator configuration
            **kwargs: Additional arguments for evaluator initialization
        """
        if key not in self.entries:
            raise KeyError(f"Evaluator '{key}' not found")
            
        try:
            evaluator_class = self.entries[key]
            
            # Update usage count
            if self.config.track_usage:
                self.info[key].usage_count += 1
            
            # Initialize with config if provided
            if config:
                return evaluator_class(config=config, **kwargs)
            return evaluator_class(**kwargs)
            
        except Exception as e:
            logger.error(f"Failed to instantiate evaluator '{key}': {str(e)}")
            raise
    
    def list_evaluators(self) -> Dict[str, Dict[str, Any]]:
        """List all registered evaluators with their info"""
        return {
            key: {
                "name": info.name,
                "description": info.description,
                "version": info.version,
                "registered_at": info.registered_at.isoformat(),
                "usage_count": info.usage_count,
                "metadata": info.metadata
            }
            for key, info in self.info.items()
        }
    
    def get_evaluator_info(self, key: str) -> EvaluatorInfo:
        """Get detailed information about a registered evaluator"""
        if key not in self.info:
            raise KeyError(f"Evaluator '{key}' not found")
        return self.info[key]
    
    def unregister(self, key: str) -> None:
        """Unregister an evaluator"""
        if key in self.entries:
            del self.entries[key]
            del self.info[key]
            logger.info(f"Unregistered evaluator '{key}'")
    
    def clear(self) -> None:
        """Clear all registered evaluators"""
        self.entries.clear()
        self.info.clear()
        logger.info("Cleared evaluator registry")
    
    def get_most_used(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most frequently used evaluators"""
        sorted_evaluators = sorted(
            self.info.items(),
            key=lambda x: x[1].usage_count,
            reverse=True
        )
        
        return [{
            "key": key,
            "name": info.name,
            "usage_count": info.usage_count,
            "version": info.version
        } for key, info in sorted_evaluators[:limit]]

# Create singleton instance
evaluator_registry = EvaluatorRegistry()

# Example usage:
"""
@evaluator_registry.register("text_quality", category="text")
class TextQualityEvaluator(BaseEvaluator):
    name = "text_quality"
    version = "1.1.0"
    # ...

# Get evaluator instance
evaluator = evaluator_registry.get(
    "text_quality",
    config=TextQualityConfig(min_score_threshold=0.7)
)

# List available evaluators
available = evaluator_registry.list_evaluators()
""" 