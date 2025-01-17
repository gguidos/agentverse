"""Chat Environment Module"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core.agentverse.interfaces import BaseEnvironment
from src.core.agentverse.agents import BaseAgent
from src.core.agentverse.message import Message, MessageType, MessageRole
from src.core.agentverse.environment.models import EnvironmentStepResult
from src.core.agentverse.exceptions import EnvironmentError

class ChatEnvironment(BaseEnvironment):
    """Chat environment implementation"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.agents: List[BaseAgent] = []
        self.history: List[Message] = []
        self.metrics: Dict[str, float] = {}
        self.step_count = 0
    
    async def step(self) -> EnvironmentStepResult:
        """Execute chat step"""
        try:
            self.step_count += 1
            
            # Check if we have agents
            if not self.agents:
                return EnvironmentStepResult(
                    output="No agents available",
                    logs=["No agents registered in environment"],
                    metrics=self.metrics,
                    done=True
                )
            
            # Get current agent
            agent_idx = (self.step_count - 1) % len(self.agents)
            current_agent = self.agents[agent_idx]
            
            # Process messages
            messages = []
            if self.history:  # Only process if we have messages
                for message in self.history[-self.config.get("context_window", 5):]:
                    response = await current_agent.process_message(message)
                    if response:
                        messages.append(response)
                        self.history.append(response)
            else:  # Generate initial message if no history
                initial_msg = Message(
                    content="Hello!",
                    type=MessageType.SYSTEM,
                    role=MessageRole.SYSTEM,
                    sender_id="system",
                    receiver_id=current_agent.name
                )
                response = await current_agent.process_message(initial_msg)
                if response:
                    messages.append(response)
                    self.history.append(response)
            
            # Update metrics
            self.metrics.update({
                "steps": self.step_count,
                "history_length": len(self.history),
                "messages_per_step": len(messages),
                "agent_count": len(self.agents)
            })
            
            # Check if done
            done = self.step_count >= self.config.get("max_rounds", 10)
            
            return EnvironmentStepResult(
                output=messages[-1].content if messages else "No messages generated",
                logs=[f"Agent {current_agent.name} processed {len(messages)} messages"],
                metrics=self.metrics,
                done=done,
                metadata={
                    "agent": current_agent.name,
                    "messages": [m.model_dump() for m in messages]
                }
            )
            
        except Exception as e:
            raise EnvironmentError(f"Failed to execute step: {str(e)}")
    
    def add_agent(self, agent: BaseAgent) -> None:
        """Add agent to environment"""
        self.agents.append(agent)
    
    async def reset(self) -> None:
        """Reset environment state"""
        self.history.clear()
        self.metrics.clear()
        self.step_count = 0
    
    async def get_metrics(self) -> Dict[str, float]:
        """Get environment metrics"""
        return self.metrics 