from typing import Dict, Any, Optional, List, ClassVar
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from string import Template
import logging

from src.core.agentverse.agents.evaluator import EvaluatorAgent, EvaluatorConfig, EvaluationMetrics
from src.core.agentverse.agents.actions import AgentAction, AgentStep
from src.core.agentverse.message.base import Message
from src.core.agentverse.memory.base import BaseMemory
from src.core.agentverse.memory.manipulators.base import BaseMemoryManipulator
from src.core.agentverse.services.llm.base import BaseLLMService
from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.registry import agent_registry
from src.core.agentverse.exceptions import AgentError

logger = logging.getLogger(__name__)

class ContinuousEvaluatorConfig(EvaluatorConfig):
    """Configuration for continuous evaluator"""
    final_round_format: str = """
    Final Evaluation:
    ${thought}
    
    Metrics:
    - Relevance: ${relevance}
    - Consistency: ${consistency}
    - Fluency: ${fluency}
    - Coherence: ${coherence}
    
    Overall Analysis: ${analysis}
    """
    history_limit: int = 10
    retry_count: int = 3
    
    model_config = ConfigDict(
        extra="allow"
    )

class ContinuousEvaluatorState(BaseModel):
    """State for continuous evaluator"""
    source_text: str = ""
    reference_text: str = ""
    generated_text: str = ""
    comparison_texts: Dict[str, str] = Field(default_factory=dict)
    current_turn: int = 0
    is_final_round: bool = False
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

@agent_registry.register("continuous_evaluator")
class ContinuousEvaluatorAgent(EvaluatorAgent):
    """Agent for continuous evaluation with memory manipulation"""
    
    name: ClassVar[str] = "continuous_evaluator"
    description: ClassVar[str] = "Continuous evaluation agent"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        llm_service: BaseLLMService,
        memory: BaseMemory,
        memory_manipulator: BaseMemoryManipulator,
        config: Optional[ContinuousEvaluatorConfig] = None
    ):
        """Initialize continuous evaluator agent"""
        super().__init__(
            llm_service=llm_service,
            memory=memory,
            config=config or ContinuousEvaluatorConfig()
        )
        self.memory_manipulator = memory_manipulator
        self.memory_manipulator.agent = self
        self.memory_manipulator.memory = self.memory
        self.continuous_state = ContinuousEvaluatorState()
        logger.info(f"Initialized {self.name} v{self.version}")
    
    async def step(
        self,
        env: BaseEnvironment,
        env_description: str = ""
    ) -> Message:
        """Process one evaluation step
        
        Args:
            env: Environment instance
            env_description: Optional environment description
            
        Returns:
            Evaluation message
            
        Raises:
            AgentError: If evaluation fails
        """
        try:
            # Update state
            self.continuous_state.current_turn = env.current_turn
            self.continuous_state.is_final_round = (
                env.current_turn >= env.max_turns - 1
            )
            
            # Create evaluation action
            action = AgentAction(
                tool="evaluate_step",
                input={
                    "turn": env.current_turn,
                    "is_final": self.continuous_state.is_final_round,
                    "env_description": env_description
                }
            )
            step = AgentStep(action=action)
            
            try:
                # Manipulate memory
                manipulated_memory = await self.memory_manipulator.manipulate_memory()
                
                # Get evaluation
                evaluation = await self._evaluate_response(
                    response=manipulated_memory,
                    context=env_description,
                    criteria={
                        "is_final": self.continuous_state.is_final_round,
                        "turn": env.current_turn,
                        "max_turns": env.max_turns
                    }
                )
                
                # Calculate metrics
                metrics = await self._calculate_metrics(evaluation)
                
                # Update action/step
                action.complete(
                    output={
                        "evaluation": evaluation,
                        "metrics": metrics.to_dict(),
                        "memory": manipulated_memory
                    },
                    duration=step.duration
                )
                step.complete({
                    "evaluation": evaluation,
                    "metrics": metrics.to_dict(),
                    "memory": manipulated_memory
                })
                
            except Exception as e:
                action.fail(str(e))
                step.fail(str(e))
                logger.error(f"Step evaluation failed: {str(e)}")
                raise
            
            # Track step
            self.action_sequence.add_step(step)
            
            # Format response
            content = self._format_step_evaluation(
                evaluation=evaluation,
                metrics=metrics,
                is_final=self.continuous_state.is_final_round
            )
            
            # Create message
            return Message(
                content=content,
                sender=self.name,
                receiver={"all"},
                metadata={
                    "turn": env.current_turn,
                    "is_final": self.continuous_state.is_final_round,
                    "metrics": metrics.to_dict(),
                    "manipulated_memory": manipulated_memory,
                    "duration": step.duration
                }
            )
            
        except Exception as e:
            logger.error(f"Evaluation step failed: {str(e)}")
            raise AgentError(
                message=f"Evaluation step failed: {str(e)}",
                details={
                    "turn": env.current_turn,
                    "is_final": self.continuous_state.is_final_round
                }
            )
    
    def _format_step_evaluation(
        self,
        evaluation: Dict[str, Any],
        metrics: EvaluationMetrics,
        is_final: bool
    ) -> str:
        """Format step evaluation
        
        Args:
            evaluation: Evaluation dictionary
            metrics: Evaluation metrics
            is_final: Whether this is final evaluation
            
        Returns:
            Formatted evaluation text
        """
        if is_final:
            return Template(self.config.final_round_format).safe_substitute({
                "thought": evaluation.get("thought", ""),
                "relevance": f"{metrics.relevance:.2f}",
                "consistency": f"{metrics.coherence:.2f}",
                "fluency": f"{metrics.accuracy:.2f}",
                "coherence": f"{metrics.completeness:.2f}",
                "analysis": evaluation.get("analysis", "")
            })
        else:
            return evaluation.get("analysis", "")
    
    async def reset(self) -> None:
        """Reset agent state"""
        await super().reset()
        self.continuous_state = ContinuousEvaluatorState()
        self.memory_manipulator.reset() 