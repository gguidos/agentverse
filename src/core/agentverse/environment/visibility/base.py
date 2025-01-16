"""Base Visibility Module"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import logging

from src.core.agentverse.environment.visibility.audit import VisibilityAudit

logger = logging.getLogger(__name__)

class VisibilityConfig(BaseModel):
    """Visibility configuration"""
    enable_audit: bool = True
    audit_logger: str = "visibility.audit"
    default_allow: bool = False

class BaseVisibility(ABC):
    """Base class for visibility control"""
    
    def __init__(self, config: Optional[VisibilityConfig] = None):
        self.config = config or VisibilityConfig()
        self.audit = (
            VisibilityAudit(self.config.audit_logger)
            if self.config.enable_audit
            else None
        )
    
    @abstractmethod
    async def is_visible(
        self,
        source: str,
        target: str,
        **kwargs
    ) -> bool:
        """Check if target is visible to source
        
        Args:
            source: Source agent/entity
            target: Target agent/entity
            **kwargs: Additional visibility options
            
        Returns:
            True if visible, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_visible_agents(
        self,
        agent_id: str,
        **kwargs
    ) -> List[str]:
        """Get list of agents visible to specified agent
        
        Args:
            agent_id: Agent identifier
            **kwargs: Additional visibility options
            
        Returns:
            List of visible agent IDs
        """
        pass
    
    async def check_access(
        self,
        source: str,
        target: str,
        resource_type: str,
        **kwargs
    ) -> bool:
        """Check access permission
        
        Args:
            source: Source agent/entity
            target: Target agent/entity
            resource_type: Type of resource
            **kwargs: Additional access options
            
        Returns:
            True if access allowed, False otherwise
        """
        try:
            # Check visibility
            is_visible = await self.is_visible(source, target, **kwargs)
            
            # Audit the check
            if self.audit:
                self.audit.log_access_check(
                    source=source,
                    target=target,
                    resource_type=resource_type,
                    allowed=is_visible,
                    **kwargs
                )
            
            return is_visible
            
        except Exception as e:
            logger.error(f"Access check failed: {str(e)}")
            return self.config.default_allow
    
    async def _log_visibility_change(
        self,
        entity: str,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        change_type: str,
        **kwargs
    ) -> None:
        """Log visibility state change
        
        Args:
            entity: Entity being changed
            old_state: Previous state
            new_state: New state
            change_type: Type of change
            **kwargs: Additional audit data
        """
        if self.audit:
            self.audit.log_visibility_change(
                entity=entity,
                old_state=old_state,
                new_state=new_state,
                change_type=change_type,
                **kwargs
            )
    
    async def _log_rule_evaluation(
        self,
        rule_id: str,
        inputs: Dict[str, Any],
        result: bool,
        **kwargs
    ) -> None:
        """Log rule evaluation
        
        Args:
            rule_id: Rule identifier
            inputs: Rule inputs
            result: Evaluation result
            **kwargs: Additional audit data
        """
        if self.audit:
            self.audit.log_rule_evaluation(
                rule_id=rule_id,
                inputs=inputs,
                result=result,
                **kwargs
            ) 