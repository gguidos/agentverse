from typing import Dict, Any, Optional, List, ClassVar
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging

from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.agents.actions import AgentAction, AgentStep, ActionSequence
from src.core.agentverse.message.base import Message
from src.core.agentverse.memory.base import BaseMemory
from src.core.agentverse.services.llm.base import BaseLLMService
from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.registry import agent_registry
from src.core.agentverse.exceptions import AgentError

logger = logging.getLogger(__name__)

class EvaluationMetrics(BaseModel):
    """Evaluation metrics"""
    relevance: float = Field(ge=0.0, le=1.0, default=0.0)
    consistency: float = Field(ge=0.0, le=1.0, default=0.0)
    fluency: float = Field(ge=0.0, le=1.0, default=0.0)
    coherence: float = Field(ge=0.0, le=1.0, default=0.0)
    
    model_config = ConfigDict(
        extra="allow"
    )

class MultiEvaluatorConfig(BaseModel):
    """Configuration for multi-evaluator"""
    metrics: List[str] = ["relevance", "consistency", "fluency", "coherence"]
    min_score: float = 0.0
    max_score: float = 1.0
    temperature: float = 0.3
    retry_count: int = 3
    track_history: bool = True
    final_round_format: str = """
    This is my final judgement!
    Thought: ${thought}
    Relevance: ${relevance}
    Consistency: ${consistency}
    Fluency: ${fluency}
    Coherence: ${coherence}
    """
    
    model_config = ConfigDict(
        extra="allow"
    )

class MultiEvaluatorState(BaseModel):
    """State for multi-evaluator"""
    source_text: str = ""
    reference_text: str = ""
    generated_text: str = ""
    comparison_texts: Dict[str, str] = Field(default_factory=dict)
    evaluations: List[Dict[str, Any]] = Field(default_factory=list)
    last_evaluation: Optional[datetime] = None
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

@agent_registry.register("multi_evaluator")
class MultiEvaluatorAgent(BaseAgent):
    """Agent for coordinating multiple LLMs for evaluation"""
    
    name: ClassVar[str] = "multi_evaluator"
    description: ClassVar[str] = "Multi-LLM evaluation coordinator"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        llm_service: BaseLLMService,
        memory: BaseMemory,
        config: Optional[MultiEvaluatorConfig] = None
    ):
        """Initialize multi-evaluator agent"""
        super().__init__(
            llm_service=llm_service,
            memory=memory,
            config=config or MultiEvaluatorConfig()
        )
        self.state = MultiEvaluatorState()
        self.action_sequence = ActionSequence()
        logger.info(f"Initialized {self.name} v{self.version}")
    
    async def step(
        self,
        env: BaseEnvironment,
        env_description: str = ""
    ) -> Message:
        """Process evaluation step
        
        Args:
            env: Environment instance
            env_description: Optional environment description
            
        Returns:
            Evaluation message
            
        Raises:
            AgentError: If evaluation fails
        """
        try:
            # Check if final round
            is_final = env.current_turn >= env.max_turns - len(env.agents)
            
            # Create evaluation action
            action = AgentAction(
                tool="evaluate",
                input={
                    "env_description": env_description,
                    "is_final": is_final,
                    "turn": env.current_turn
                }
            )
            step = AgentStep(action=action)
            
            try:
                # Get evaluation
                evaluation = await self._get_evaluation_with_retry(
                    env=env,
                    is_final=is_final
                )
                
                # Update action/step
                action.complete(
                    output=evaluation,
                    duration=step.duration
                )
                step.complete(evaluation)
                
                # Track evaluation
                if self.config.track_history:
                    self.state.evaluations.append({
                        "evaluation": evaluation,
                        "turn": env.current_turn,
                        "is_final": is_final,
                        "timestamp": datetime.utcnow()
                    })
                
            except Exception as e:
                action.fail(str(e))
                step.fail(str(e))
                logger.error(f"Evaluation failed: {str(e)}")
                raise
            
            # Track step
            self.action_sequence.add_step(step)
            
            # Format response
            content = self._format_evaluation(evaluation, is_final)
            
            # Create message
            return Message(
                content=content,
                sender=self.name,
                receiver={"all"},
                metadata={
                    "is_final": is_final,
                    "turn": env.current_turn,
                    "metrics": evaluation.get("metrics", {}),
                    "duration": step.duration
                }
            )
            
        except Exception as e:
            logger.error(f"Evaluation step failed: {str(e)}")
            raise AgentError(
                message=f"Evaluation step failed: {str(e)}",
                details={
                    "turn": env.current_turn,
                    "is_final": is_final if 'is_final' in locals() else None
                }
            )
    
    async def _get_evaluation_with_retry(
        self,
        env: BaseEnvironment,
        is_final: bool,
        attempt: int = 0
    ) -> Dict[str, Any]:
        """Get evaluation with retry logic
        
        Args:
            env: Environment instance
            is_final: Whether this is final evaluation
            attempt: Current attempt number
            
        Returns:
            Evaluation result
            
        Raises:
            AgentError: If evaluation fails
        """
        try:
            # Build prompt
            prompt = self._build_prompt(
                env_description=env.description,
                is_final=is_final
            )
            
            # Get history
            history = await self.memory.get_messages(
                limit=self.config.history_limit
            )
            
            # Get evaluation
            response = await self.llm.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": self.config.system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ] + [msg.to_dict() for msg in history],
                temperature=self.config.temperature
            )
            
            # Parse evaluation
            evaluation = self._parse_evaluation(
                response.choices[0].message.content,
                is_final
            )
            
            return evaluation
            
        except Exception as e:
            if attempt < self.config.retry_count - 1:
                logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                return await self._get_evaluation_with_retry(
                    env=env,
                    is_final=is_final,
                    attempt=attempt + 1
                )
            else:
                logger.error(f"All retry attempts failed: {str(e)}")
                raise AgentError(
                    message=f"Failed to get evaluation: {str(e)}",
                    details={
                        "attempts": attempt + 1,
                        "is_final": is_final
                    }
                )
    
    def _build_prompt(
        self,
        env_description: str,
        is_final: bool
    ) -> str:
        """Build evaluation prompt
        
        Args:
            env_description: Environment description
            is_final: Whether this is final evaluation
            
        Returns:
            Prompt text
        """
        template_vars = {
            "agent_name": self.name,
            "env_description": env_description,
            "role_description": self.config.role_description,
            "source_text": self.state.source_text,
            "reference_text": self.state.reference_text,
            "generated_text": self.state.generated_text,
            "metrics": ", ".join(self.config.metrics)
        }
        
        if is_final:
            template_vars["final_format"] = self.config.final_round_format
        
        from string import Template
        return Template(self.config.prompt_template).safe_substitute(template_vars)
    
    def _parse_evaluation(
        self,
        text: str,
        is_final: bool
    ) -> Dict[str, Any]:
        """Parse evaluation text
        
        Args:
            text: Evaluation text
            is_final: Whether this is final evaluation
            
        Returns:
            Parsed evaluation
        """
        evaluation = {
            "text": text,
            "metrics": {},
            "is_final": is_final
        }
        
        # Extract metrics
        for metric in self.config.metrics:
            if metric.lower() in text.lower():
                try:
                    # Simple extraction - could be improved
                    score = float(
                        text.lower()
                        .split(f"{metric.lower()}:")[1]
                        .split()[0]
                    )
                    evaluation["metrics"][metric] = min(
                        max(score, self.config.min_score),
                        self.config.max_score
                    )
                except:
                    pass
        
        return evaluation
    
    def _format_evaluation(
        self,
        evaluation: Dict[str, Any],
        is_final: bool
    ) -> str:
        """Format evaluation output
        
        Args:
            evaluation: Evaluation dictionary
            is_final: Whether this is final evaluation
            
        Returns:
            Formatted text
        """
        if is_final:
            from string import Template
            return Template(self.config.final_round_format).safe_substitute({
                "thought": evaluation.get("text", ""),
                "relevance": f"{evaluation['metrics'].get('relevance', 0):.2f}",
                "consistency": f"{evaluation['metrics'].get('consistency', 0):.2f}",
                "fluency": f"{evaluation['metrics'].get('fluency', 0):.2f}",
                "coherence": f"{evaluation['metrics'].get('coherence', 0):.2f}"
            })
        else:
            return evaluation.get("text", "")
    
    async def aggregate_evaluations(
        self,
        evaluations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate evaluations from multiple agents
        
        Args:
            evaluations: List of evaluations
            
        Returns:
            Aggregated results
            
        Raises:
            AgentError: If aggregation fails
        """
        try:
            # Initialize scores
            aggregated_scores = {
                metric: 0.0 for metric in self.config.metrics
            }
            
            # Sum scores
            for eval in evaluations:
                for metric, score in eval.get("metrics", {}).items():
                    if metric in aggregated_scores:
                        aggregated_scores[metric] += score
            
            # Average scores
            agent_count = len(evaluations)
            for metric in aggregated_scores:
                aggregated_scores[metric] /= agent_count
            
            return {
                "aggregated_scores": aggregated_scores,
                "overall_score": (
                    sum(aggregated_scores.values()) /
                    len(self.config.metrics)
                ),
                "individual_evaluations": evaluations
            }
            
        except Exception as e:
            logger.error(f"Evaluation aggregation failed: {str(e)}")
            raise AgentError(
                message=f"Failed to aggregate evaluations: {str(e)}",
                details={"evaluation_count": len(evaluations)}
            )
    
    async def reset(self) -> None:
        """Reset agent state"""
        await super().reset()
        self.state = MultiEvaluatorState()
        self.action_sequence = ActionSequence() 