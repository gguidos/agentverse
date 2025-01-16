from typing import Optional, List, Dict, Any, ClassVar, Set
from pydantic import BaseModel, Field, ConfigDict
import random
import logging
from datetime import datetime

from src.core.agentverse.environment.orders.base import (
    BaseOrder,
    OrderConfig,
    OrderResult
)
from src.core.agentverse.environment.registry import order_registry
from src.core.agentverse.environment.exceptions import ActionError

logger = logging.getLogger(__name__)

class RandomOrderConfig(OrderConfig):
    """Configuration for random order"""
    seed: Optional[int] = None
    choices: Optional[List[str]] = None
    weights: Optional[List[float]] = None
    exclude_recent: bool = True
    recent_memory: int = 3
    allow_repeats: bool = False
    
    model_config = ConfigDict(
        extra="allow"
    )

class RandomOrderMetrics(BaseModel):
    """Metrics for random selection"""
    total_selections: int = 0
    unique_selections: int = 0
    selection_counts: Dict[str, int] = Field(default_factory=dict)
    recent_selections: List[str] = Field(default_factory=list)

@order_registry.register("random")
class RandomOrder(BaseOrder):
    """Order for random selection with advanced features"""
    
    name: ClassVar[str] = "random_order"
    description: ClassVar[str] = "Order for random selection with weights and memory"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        config: Optional[RandomOrderConfig] = None
    ):
        super().__init__(config=config or RandomOrderConfig())
        self.random_metrics = RandomOrderMetrics()
        
        # Initialize random state
        if self.config.seed is not None:
            random.seed(self.config.seed)
            logger.info(f"Initialized random order with seed: {self.config.seed}")
    
    async def _execute(
        self,
        state: Dict[str, Any],
        choices: Optional[List[str]] = None,
        weights: Optional[List[float]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute random selection
        
        Args:
            state: Current environment state
            choices: Optional list of choices to select from
            weights: Optional weights for choices
            **kwargs: Additional arguments
            
        Returns:
            Updated state with selection
            
        Raises:
            ActionError: If selection fails
        """
        try:
            # Get available choices
            available_choices = self._get_available_choices(
                state=state,
                choices=choices
            )
            
            if not available_choices:
                raise ValueError("No choices available for random selection")
            
            # Get weights
            selection_weights = self._get_weights(
                choices=available_choices,
                weights=weights
            )
            
            # Make selection
            selected = random.choices(
                population=list(available_choices),
                weights=selection_weights,
                k=1
            )[0]
            
            # Update state
            new_state = self._update_state_with_selection(
                state=state.copy(),
                selected=selected
            )
            
            # Update metrics
            self._update_selection_metrics(selected)
            
            return new_state
            
        except Exception as e:
            logger.error(f"Random selection failed: {str(e)}")
            raise ActionError(
                message=str(e),
                action=self.name,
                details={
                    "choices": choices,
                    "weights": weights,
                    "state": state
                }
            )
    
    def _get_available_choices(
        self,
        state: Dict[str, Any],
        choices: Optional[List[str]] = None
    ) -> Set[str]:
        """Get available choices for selection
        
        Args:
            state: Current state
            choices: Optional choices override
            
        Returns:
            Set of available choices
        """
        # Get base choices
        available = set(
            choices or
            self.config.choices or
            state.get("choices", [])
        )
        
        # Exclude recent if configured
        if (
            self.config.exclude_recent and
            not self.config.allow_repeats and
            self.random_metrics.recent_selections
        ):
            recent = set(
                self.random_metrics.recent_selections[
                    -self.config.recent_memory:
                ]
            )
            available -= recent
        
        return available
    
    def _get_weights(
        self,
        choices: Set[str],
        weights: Optional[List[float]] = None
    ) -> List[float]:
        """Get weights for choices
        
        Args:
            choices: Available choices
            weights: Optional weights override
            
        Returns:
            List of weights
        """
        if weights:
            if len(weights) != len(choices):
                raise ValueError(
                    f"Number of weights ({len(weights)}) must match "
                    f"number of choices ({len(choices)})"
                )
            return weights
            
        if self.config.weights:
            if len(self.config.weights) != len(choices):
                raise ValueError(
                    f"Number of configured weights ({len(self.config.weights)}) "
                    f"must match number of choices ({len(choices)})"
                )
            return self.config.weights
            
        return [1.0] * len(choices)
    
    def _update_state_with_selection(
        self,
        state: Dict[str, Any],
        selected: str
    ) -> Dict[str, Any]:
        """Update state with selection
        
        Args:
            state: Current state
            selected: Selected choice
            
        Returns:
            Updated state
        """
        state["last_selection"] = selected
        state["selection_history"] = (
            state.get("selection_history", []) + [selected]
        )
        state["last_selection_time"] = datetime.utcnow().isoformat()
        
        return state
    
    def _update_selection_metrics(
        self,
        selected: str
    ) -> None:
        """Update selection metrics
        
        Args:
            selected: Selected choice
        """
        self.random_metrics.total_selections += 1
        
        # Update counts
        if selected not in self.random_metrics.selection_counts:
            self.random_metrics.unique_selections += 1
        self.random_metrics.selection_counts[selected] = (
            self.random_metrics.selection_counts.get(selected, 0) + 1
        )
        
        # Update recent selections
        self.random_metrics.recent_selections.append(selected)
        if len(self.random_metrics.recent_selections) > self.config.recent_memory:
            self.random_metrics.recent_selections.pop(0)
    
    async def validate(
        self,
        state: Dict[str, Any]
    ) -> bool:
        """Validate if random selection is possible
        
        Args:
            state: Current state
            
        Returns:
            Whether selection is possible
        """
        try:
            available = self._get_available_choices(state)
            return bool(available)
        except Exception:
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics including random metrics"""
        metrics = super().get_metrics()
        random_metrics = self.random_metrics.model_dump()
        
        # Add distribution metrics
        if self.random_metrics.total_selections > 0:
            total = self.random_metrics.total_selections
            distribution = {
                choice: count / total
                for choice, count in self.random_metrics.selection_counts.items()
            }
            random_metrics["distribution"] = distribution
        
        metrics.update(random_metrics)
        return metrics
    
    def reset(self) -> None:
        """Reset order state"""
        super().reset()
        self.random_metrics = RandomOrderMetrics()
        
        # Reseed if configured
        if self.config.seed is not None:
            random.seed(self.config.seed)
        
        logger.info(f"Reset {self.name} order") 