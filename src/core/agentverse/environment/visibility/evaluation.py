from typing import Set, Dict, Any, Optional, ClassVar
from pydantic import Field, ConfigDict
from datetime import datetime
import logging

from src.core.agentverse.environment.visibility.base import (
    BaseVisibility,
    VisibilityConfig,
    VisibilityMetrics
)
from src.core.agentverse.environment.registry import visibility_registry
from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.environment.exceptions import ActionError

logger = logging.getLogger(__name__)

class EvaluationVisibilityConfig(VisibilityConfig):
    """Configuration for evaluation visibility"""
    blind_final_rounds: bool = True
    final_round_count: Optional[int] = None
    track_phase_changes: bool = True
    allow_self_visibility: bool = True
    broadcast_phase_change: bool = True
    
    model_config = ConfigDict(
        extra="allow"
    )

class EvaluationMetrics(VisibilityMetrics):
    """Additional metrics for evaluation visibility"""
    phase_changes: int = 0
    blind_rounds: int = 0
    full_rounds: int = 0
    phase_durations: Dict[str, float] = Field(default_factory=dict)

@visibility_registry.register("blind_judge")
class BlindJudgeVisibility(BaseVisibility):
    """Visibility handler for blind evaluation rounds
    
    In final rounds, each judge can only see their own messages
    to ensure independent evaluation.
    """
    
    name: ClassVar[str] = "blind_judge_visibility"
    description: ClassVar[str] = "Visibility handler for blind evaluation rounds"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        config: Optional[EvaluationVisibilityConfig] = None
    ):
        super().__init__(config=config or EvaluationVisibilityConfig())
        self.eval_metrics = EvaluationMetrics()
        self.current_phase: str = "full"
        self.phase_start: Optional[datetime] = None
    
    async def _update_visibility(
        self,
        environment: BaseEnvironment
    ) -> None:
        """Update agent visibility based on turn number
        
        Args:
            environment: Environment to update visibility for
            
        Raises:
            ActionError: If update fails
        """
        try:
            # Determine phase
            new_phase = self._get_current_phase(environment)
            
            # Track phase change
            if new_phase != self.current_phase:
                await self._handle_phase_change(
                    environment,
                    new_phase
                )
            
            # Update visibility based on phase
            if new_phase == "blind":
                await self._set_blind_visibility(environment)
            else:
                await self._set_full_visibility(environment)
            
        except Exception as e:
            logger.error(f"Failed to update judge visibility: {str(e)}")
            raise ActionError(
                message=str(e),
                action=self.name,
                details={
                    "phase": self.current_phase,
                    "turn": environment.state.current_turn
                }
            )
    
    def _get_current_phase(
        self,
        environment: BaseEnvironment
    ) -> str:
        """Determine current visibility phase
        
        Args:
            environment: Environment instance
            
        Returns:
            Current phase ("blind" or "full")
        """
        if not self.config.blind_final_rounds:
            return "full"
            
        final_rounds = (
            self.config.final_round_count or
            len(environment.agents)
        )
        
        if environment.state.max_turns:
            remaining = environment.state.max_turns - environment.state.current_turn
            return "blind" if remaining <= final_rounds else "full"
            
        return "full"
    
    async def _handle_phase_change(
        self,
        environment: BaseEnvironment,
        new_phase: str
    ) -> None:
        """Handle visibility phase change
        
        Args:
            environment: Environment instance
            new_phase: New visibility phase
        """
        if self.config.track_phase_changes:
            # Track phase duration
            if self.phase_start:
                duration = (datetime.utcnow() - self.phase_start).total_seconds()
                self.eval_metrics.phase_durations[self.current_phase] = duration
            
            self.eval_metrics.phase_changes += 1
            
        # Update phase tracking
        self.current_phase = new_phase
        self.phase_start = datetime.utcnow()
        
        # Broadcast phase change if configured
        if self.config.broadcast_phase_change:
            await self._broadcast_phase_change(environment)
    
    async def _broadcast_phase_change(
        self,
        environment: BaseEnvironment
    ) -> None:
        """Broadcast phase change to agents
        
        Args:
            environment: Environment instance
        """
        for agent in environment.agents:
            if hasattr(agent, 'on_visibility_change'):
                await agent.on_visibility_change(
                    phase=self.current_phase,
                    visible_agents=self.state.visibility_map.get(
                        agent.name,
                        set()
                    )
                )
    
    async def _set_blind_visibility(
        self,
        environment: BaseEnvironment
    ) -> None:
        """Set judges to only see their own messages
        
        Args:
            environment: Environment instance
        """
        self.eval_metrics.blind_rounds += 1
        
        for agent in environment.agents:
            visible = {agent.name} if self.config.allow_self_visibility else set()
            self.state.visibility_map[agent.name] = visible
            
            # Update agent's receiver set if supported
            if hasattr(agent, 'set_receiver'):
                await agent.set_receiver(visible)
    
    async def _set_full_visibility(
        self,
        environment: BaseEnvironment
    ) -> None:
        """Set full visibility between agents
        
        Args:
            environment: Environment instance
        """
        self.eval_metrics.full_rounds += 1
        agent_names = {agent.name for agent in environment.agents}
        
        for agent in environment.agents:
            # Can see everyone (optionally except self)
            visible = (
                agent_names if self.config.allow_self_visibility
                else agent_names - {agent.name}
            )
            self.state.visibility_map[agent.name] = visible
            
            # Update agent's receiver set if supported
            if hasattr(agent, 'set_receiver'):
                await agent.set_receiver(visible)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics including evaluation metrics
        
        Returns:
            Combined metrics
        """
        metrics = super().get_metrics()
        eval_metrics = self.eval_metrics.model_dump()
        
        # Add phase distribution
        total_rounds = (
            self.eval_metrics.blind_rounds +
            self.eval_metrics.full_rounds
        )
        if total_rounds > 0:
            eval_metrics["blind_phase_ratio"] = (
                self.eval_metrics.blind_rounds / total_rounds
            )
        
        metrics.update(eval_metrics)
        return metrics
    
    def reset(self) -> None:
        """Reset visibility state"""
        super().reset()
        self.eval_metrics = EvaluationMetrics()
        self.current_phase = "full"
        self.phase_start = None
        logger.info(
            f"Reset {self.name} visibility handler "
            f"(phase: {self.current_phase})"
        ) 