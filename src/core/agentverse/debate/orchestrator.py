import asyncio
from typing import Dict, Any
from src.core.agentverse.agents.judge_agent import JudgeAgent
from src.core.agentverse.agents.evaluator import EvaluatorAgent

class DebateOrchestrator:
    """Orchestrates debates between evaluator agents"""
    
    def __init__(
        self,
        judge: JudgeAgent,
        evaluators: Dict[str, EvaluatorAgent]
    ):
        self.judge = judge
        self.evaluators = evaluators
        
    async def start_debate(
        self,
        topic: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Start a new debate"""
        # Start debate with judge
        debate_id = await self.judge.start_debate(topic, context)
        
        # Get evaluations from all evaluators
        evaluation_tasks = []
        for evaluator_id, evaluator in self.evaluators.items():
            task = asyncio.create_task(
                self._get_evaluation(
                    debate_id,
                    evaluator_id,
                    evaluator,
                    topic,
                    context
                )
            )
            evaluation_tasks.append(task)
            
        # Wait for evaluations
        await asyncio.gather(*evaluation_tasks)
        
        # Wait for judgement
        debate = await self._wait_for_judgement(debate_id)
        return debate
        
    async def _get_evaluation(
        self,
        debate_id: str,
        evaluator_id: str,
        evaluator: EvaluatorAgent,
        topic: str,
        context: Dict[str, Any]
    ) -> None:
        """Get evaluation from single evaluator"""
        evaluation = await evaluator.evaluate(topic, context)
        await self.judge.receive_evaluation(debate_id, evaluator_id, evaluation) 