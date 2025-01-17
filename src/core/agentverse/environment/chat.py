"""Chat environment implementation"""

from typing import Dict, Any, List
from datetime import datetime
from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.environment.models import EnvironmentStepResult

class ChatEnvironment(BaseEnvironment):
    """Chat environment for agent interactions"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.max_rounds = config.get("max_rounds", 10)
        self.context_window = config.get("context_window", 5)
        self.current_round = 0
        self.messages = []
        
    async def step(self) -> EnvironmentStepResult:
        """Execute one chat round"""
        self.current_round += 1
        return EnvironmentStepResult(
            output="Chat step executed",
            logs=[f"Round {self.current_round} completed"],
            metrics=await self.get_metrics(),
            done=self.current_round >= self.max_rounds,
            metadata={
                "agent": "chat_environment",
                "round": self.current_round
            },
            timestamp=datetime.utcnow()
        )
        
    async def reset(self) -> None:
        """Reset chat state"""
        self.current_round = 0
        self.messages = []
        
    async def get_metrics(self) -> Dict[str, Any]:
        """Get chat metrics"""
        return {
            "rounds": self.current_round,
            "messages": len(self.messages)
        } 