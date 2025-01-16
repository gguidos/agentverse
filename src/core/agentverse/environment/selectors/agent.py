"""Agent Selector Module"""

from typing import Dict, Any, Optional, List
from src.core.agentverse.environment.selectors.base import BaseSelector

class AgentSelector(BaseSelector):
    """Agent selection logic"""
    
    async def select(
        self,
        candidates: List[Dict[str, Any]],
        required_capabilities: Optional[List[str]] = None,
        count: int = 1,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Select agents based on capabilities
        
        Args:
            candidates: List of agent configurations
            required_capabilities: Required agent capabilities
            count: Number of agents to select
            **kwargs: Additional selection criteria
            
        Returns:
            Selected agents
        """
        try:
            # Score all candidates
            scored_agents = []
            for agent in candidates:
                score = await self.score(
                    agent,
                    required_capabilities=required_capabilities,
                    **kwargs
                )
                if score >= self.config.min_score:
                    scored_agents.append((score, agent))
            
            # Sort by score and select top agents
            scored_agents.sort(reverse=True)
            selected = [agent for _, agent in scored_agents[:count]]
            
            return selected
            
        except Exception as e:
            logger.error(f"Agent selection failed: {str(e)}")
            raise
    
    async def score(
        self,
        agent: Dict[str, Any],
        required_capabilities: Optional[List[str]] = None,
        **kwargs
    ) -> float:
        """Score agent based on capabilities
        
        Args:
            agent: Agent configuration
            required_capabilities: Required capabilities
            **kwargs: Additional scoring criteria
            
        Returns:
            Score between 0 and 1
        """
        if not required_capabilities:
            return 1.0
            
        agent_capabilities = set(agent.get("capabilities", []))
        required = set(required_capabilities)
        
        if not required:
            return 1.0
            
        # Calculate capability match ratio
        matches = len(required.intersection(agent_capabilities))
        score = matches / len(required)
        
        return score 