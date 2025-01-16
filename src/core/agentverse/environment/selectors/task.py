"""Task Selector Module"""

from typing import Dict, Any, Optional, List
from src.core.agentverse.environment.selectors.base import BaseSelector

class TaskSelector(BaseSelector):
    """Task selection logic"""
    
    async def select(
        self,
        candidates: List[Dict[str, Any]],
        priority: Optional[str] = None,
        agent_id: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Select tasks based on priority and agent
        
        Args:
            candidates: List of tasks
            priority: Task priority level
            agent_id: Agent identifier
            **kwargs: Additional selection criteria
            
        Returns:
            Selected tasks
        """
        try:
            # Score tasks
            scored_tasks = []
            for task in candidates:
                score = await self.score(
                    task,
                    priority=priority,
                    agent_id=agent_id,
                    **kwargs
                )
                if score >= self.config.min_score:
                    scored_tasks.append((score, task))
            
            # Sort and select tasks
            scored_tasks.sort(reverse=True)
            selected = [t for _, t in scored_tasks[:self.config.max_results]]
            
            return selected
            
        except Exception as e:
            logger.error(f"Task selection failed: {str(e)}")
            raise
    
    async def score(
        self,
        task: Dict[str, Any],
        priority: Optional[str] = None,
        agent_id: Optional[str] = None,
        **kwargs
    ) -> float:
        """Score task based on criteria
        
        Args:
            task: Task configuration
            priority: Required priority
            agent_id: Agent identifier
            **kwargs: Additional scoring criteria
            
        Returns:
            Score between 0 and 1
        """
        score = 1.0
        
        # Check priority match
        if priority and task.get("priority") != priority:
            score *= 0.5
            
        # Check agent assignment
        if agent_id and task.get("assigned_to") != agent_id:
            score *= 0.5
            
        return score 