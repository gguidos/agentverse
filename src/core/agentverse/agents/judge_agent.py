from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging
from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.agents.evaluator import EvaluationResult
from src.core.agentverse.message import Message, MessageType
from src.core.agentverse.registry import agent_registry

logger = logging.getLogger(__name__)

class JudgementCriteria(BaseModel):
    """Criteria for making judgements"""
    min_evaluators: int = 2
    consensus_threshold: float = 0.7
    weighting_scheme: Dict[str, float] = {}  # weights for different evaluator types
    required_perspectives: List[str] = []  # must have these evaluator types

class JudgeConfig(BaseModel):
    """Configuration for judge agent"""
    criteria: JudgementCriteria = Field(default_factory=JudgementCriteria)
    debate_timeout: float = 30.0  # seconds to wait for all evaluations
    resolution_strategy: str = "consensus"  # consensus, majority, weighted

@agent_registry.register("judge")
class JudgeAgent(BaseAgent):
    """Agent that synthesizes multiple evaluations into final judgements"""
    
    name = "judge"
    description = "Synthesizes evaluations and makes final judgements"
    version = "1.0.0"
    
    def __init__(self, config: JudgeConfig):
        super().__init__(config)
        self.criteria = config.criteria
        self.active_debates: Dict[str, Dict[str, Any]] = {}
        
    async def start_debate(self, topic: str, context: Dict[str, Any]) -> str:
        """Start a new debate topic"""
        debate_id = str(uuid.uuid4())
        self.active_debates[debate_id] = {
            "topic": topic,
            "context": context,
            "evaluations": {},
            "status": "active",
            "started_at": datetime.utcnow()
        }
        return debate_id
        
    async def receive_evaluation(
        self,
        debate_id: str,
        evaluator_id: str,
        evaluation: EvaluationResult
    ) -> None:
        """Receive an evaluation for an active debate"""
        if debate_id not in self.active_debates:
            raise ValueError(f"No active debate found with id {debate_id}")
            
        debate = self.active_debates[debate_id]
        debate["evaluations"][evaluator_id] = evaluation
        
        # Check if we have enough evaluations to make a judgement
        if self._can_make_judgement(debate):
            await self._make_judgement(debate_id)
            
    async def _make_judgement(self, debate_id: str) -> Dict[str, Any]:
        """Synthesize evaluations and make final judgement"""
        debate = self.active_debates[debate_id]
        evaluations = debate["evaluations"]
        
        # Prepare prompt with all evaluations
        prompt = f"""
        Topic: {debate["topic"]}
        
        Context: {debate["context"]}
        
        Evaluations from different perspectives:
        
        {self._format_evaluations(evaluations)}
        
        Consider the following in your judgement:
        1. Consensus among evaluators
        2. Strength of arguments
        3. Supporting evidence
        4. Different perspectives presented
        
        Provide:
        1. Final judgement
        2. Key points of agreement
        3. Notable dissenting views
        4. Confidence level
        5. Reasoning for decision
        """
        
        response = await self.llm.generate(prompt)
        judgement = self._parse_judgement(response)
        
        # Update debate status
        debate["status"] = "completed"
        debate["judgement"] = judgement
        debate["completed_at"] = datetime.utcnow()
        
        # Notify about judgement
        await self._notify_judgement(debate_id, judgement)
        
        return judgement
        
    def _can_make_judgement(self, debate: Dict[str, Any]) -> bool:
        """Check if we can make a judgement based on criteria"""
        evaluations = debate["evaluations"]
        
        # Check minimum number of evaluators
        if len(evaluations) < self.criteria.min_evaluators:
            return False
            
        # Check required perspectives
        evaluator_types = set(e.metadata.get("evaluator_type") 
                            for e in evaluations.values())
        missing_perspectives = set(self.criteria.required_perspectives) - evaluator_types
        if missing_perspectives:
            return False
            
        return True
        
    def _format_evaluations(self, evaluations: Dict[str, EvaluationResult]) -> str:
        """Format evaluations for LLM prompt"""
        formatted = []
        for evaluator_id, eval_result in evaluations.items():
            formatted.append(f"""
            Evaluator: {evaluator_id} ({eval_result.metadata.get('evaluator_type', 'unknown')})
            Assessment: {eval_result.feedback}
            Confidence: {eval_result.metrics.confidence}
            Key Points:
            {self._format_points(eval_result.metadata.get('key_points', []))}
            """)
        return "\n".join(formatted)
        
    async def _notify_judgement(self, debate_id: str, judgement: Dict[str, Any]) -> None:
        """Notify interested parties about the judgement"""
        message = Message(
            content=judgement["summary"],
            type=MessageType.EVENT,
            sender=self.name,
            metadata={
                "event_type": "judgement_made",
                "debate_id": debate_id,
                "judgement": judgement
            }
        )
        await self.message_bus.publish(message) 