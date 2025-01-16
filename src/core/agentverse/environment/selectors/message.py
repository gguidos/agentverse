"""Message Selector Module"""

from typing import Dict, Any, Optional, List
from src.core.agentverse.environment.selectors.base import BaseSelector

class MessageSelector(BaseSelector):
    """Message selection logic"""
    
    async def select(
        self,
        candidates: List[Dict[str, Any]],
        agent_id: Optional[str] = None,
        message_type: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Select messages based on criteria
        
        Args:
            candidates: List of messages
            agent_id: Agent identifier
            message_type: Message type filter
            **kwargs: Additional selection criteria
            
        Returns:
            Selected messages
        """
        try:
            # Score messages
            scored_messages = []
            for message in candidates:
                score = await self.score(
                    message,
                    agent_id=agent_id,
                    message_type=message_type,
                    **kwargs
                )
                if score >= self.config.min_score:
                    scored_messages.append((score, message))
            
            # Sort and select messages
            scored_messages.sort(reverse=True)
            selected = [m for _, m in scored_messages[:self.config.max_results]]
            
            return selected
            
        except Exception as e:
            logger.error(f"Message selection failed: {str(e)}")
            raise
    
    async def score(
        self,
        message: Dict[str, Any],
        agent_id: Optional[str] = None,
        message_type: Optional[str] = None,
        **kwargs
    ) -> float:
        """Score message based on criteria
        
        Args:
            message: Message data
            agent_id: Agent identifier
            message_type: Message type
            **kwargs: Additional scoring criteria
            
        Returns:
            Score between 0 and 1
        """
        score = 1.0
        
        # Check agent match
        if agent_id:
            if message.get("to") != agent_id:
                score *= 0.5
                
        # Check message type
        if message_type:
            if message.get("type") != message_type:
                score *= 0.5
                
        return score 