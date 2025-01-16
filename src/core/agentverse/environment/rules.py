from typing import Dict, Any, Optional, List, Set, ClassVar
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging
from abc import ABC, abstractmethod

from src.core.agentverse.environment.exceptions import RuleValidationError

logger = logging.getLogger(__name__)

class RuleConfig(BaseModel):
    """Configuration for environment rules"""
    order: Dict[str, Any] = Field(
        default_factory=lambda: {"type": "sequential"}
    )
    visibility: Dict[str, Any] = Field(
        default_factory=lambda: {"type": "all"}
    )
    selector: Dict[str, Any] = Field(
        default_factory=lambda: {"type": "basic"}
    )
    updater: Dict[str, Any] = Field(
        default_factory=lambda: {"type": "basic"}
    )
    describer: Dict[str, Any] = Field(
        default_factory=lambda: {"type": "basic"}
    )
    
    model_config = ConfigDict(
        extra="allow"
    )

class RuleMetrics(BaseModel):
    """Metrics for rule execution"""
    applications: int = 0
    validations: int = 0
    failures: int = 0
    last_execution: Optional[datetime] = None
    execution_times: List[float] = Field(default_factory=list)

class Rule(ABC):
    """Base class for environment rules"""
    
    name: ClassVar[str] = "base_rule"
    description: ClassVar[str] = "Base rule implementation"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        order_config: Dict[str, Any],
        visibility_config: Dict[str, Any],
        selector_config: Dict[str, Any],
        updater_config: Dict[str, Any],
        describer_config: Dict[str, Any]
    ):
        self.order_config = order_config
        self.visibility_config = visibility_config
        self.selector_config = selector_config
        self.updater_config = updater_config
        self.describer_config = describer_config
        
        self.metrics = RuleMetrics()
        self._validate_configs()
        
        logger.info(f"Initialized {self.name} rule v{self.version}")
    
    def _validate_configs(self) -> None:
        """Validate rule configurations"""
        configs = {
            "order": self.order_config,
            "visibility": self.visibility_config,
            "selector": self.selector_config,
            "updater": self.updater_config,
            "describer": self.describer_config
        }
        
        for name, config in configs.items():
            if not isinstance(config, dict):
                raise RuleValidationError(
                    message=f"Invalid {name} configuration",
                    rule_name=self.name,
                    validation_details={"config": config}
                )
            if "type" not in config:
                raise RuleValidationError(
                    message=f"Missing type in {name} configuration",
                    rule_name=self.name,
                    validation_details={"config": config}
                )
    
    @abstractmethod
    async def validate(self, state: Dict[str, Any]) -> bool:
        """Validate if the current state follows the rule
        
        Args:
            state: Current environment state
            
        Returns:
            bool: Whether state is valid
            
        Raises:
            RuleValidationError: If validation fails
        """
        self.metrics.validations += 1
        return True
    
    @abstractmethod
    async def apply(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply the rule to the current state
        
        Args:
            state: Current environment state
            
        Returns:
            Dict: Updated state
            
        Raises:
            RuleValidationError: If rule application fails
        """
        start_time = datetime.utcnow()
        try:
            self.metrics.applications += 1
            return state
        except Exception as e:
            self.metrics.failures += 1
            raise RuleValidationError(
                message=f"Rule application failed: {str(e)}",
                rule_name=self.name,
                validation_details={"state": state}
            )
        finally:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.execution_times.append(duration)
            self.metrics.last_execution = datetime.utcnow()
    
    async def describe(self, state: Dict[str, Any]) -> str:
        """Describe the current state according to the rule
        
        Args:
            state: Current environment state
            
        Returns:
            str: State description
        """
        try:
            description = f"Environment state with {len(state)} items"
            if "agents" in state:
                description += f"\nAgents: {len(state['agents'])}"
            if "messages" in state:
                description += f"\nMessages: {len(state['messages'])}"
            return description
        except Exception as e:
            logger.error(f"Failed to describe state: {str(e)}")
            return "Failed to describe state"
    
    async def select_next(self, state: Dict[str, Any]) -> Optional[str]:
        """Select next agent according to order rules
        
        Args:
            state: Current environment state
            
        Returns:
            Optional[str]: ID of next agent
        """
        try:
            agents = state.get("agents", [])
            if not agents:
                return None
                
            order_type = self.order_config["type"]
            
            if order_type == "sequential":
                current = state.get("current_agent_index", -1)
                next_index = (current + 1) % len(agents)
                state["current_agent_index"] = next_index
                return agents[next_index]
                
            elif order_type == "random":
                import random
                return random.choice(agents)
                
            else:
                logger.warning(f"Unknown order type: {order_type}")
                return agents[0]
                
        except Exception as e:
            logger.error(f"Failed to select next agent: {str(e)}")
            return None
    
    async def update_state(
        self,
        state: Dict[str, Any],
        update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update state according to rules
        
        Args:
            state: Current environment state
            update: State updates
            
        Returns:
            Dict: Updated state
            
        Raises:
            RuleValidationError: If update fails
        """
        try:
            # Apply updates
            for key, value in update.items():
                if key in state:
                    if isinstance(state[key], dict) and isinstance(value, dict):
                        state[key].update(value)
                    elif isinstance(state[key], list) and isinstance(value, list):
                        state[key].extend(value)
                    else:
                        state[key] = value
                else:
                    state[key] = value
            
            # Validate updated state
            if not await self.validate(state):
                raise ValueError("Invalid state after update")
            
            return state
            
        except Exception as e:
            raise RuleValidationError(
                message=f"State update failed: {str(e)}",
                rule_name=self.name,
                validation_details={
                    "state": state,
                    "update": update
                }
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get rule execution metrics"""
        metrics = self.metrics.model_dump()
        if self.metrics.execution_times:
            metrics["avg_execution_time"] = (
                sum(self.metrics.execution_times) /
                len(self.metrics.execution_times)
            )
        return metrics
    
    def __str__(self) -> str:
        return f"{self.name}Rule(v{self.version})"
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"order={self.order_config['type']}, "
            f"visibility={self.visibility_config['type']}, "
            f"applications={self.metrics.applications})"
        ) 