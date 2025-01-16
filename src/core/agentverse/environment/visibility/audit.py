"""Visibility Audit Module"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging
import json

from src.core.agentverse.environment.visibility.storage import (
    AuditStorage,
    MongoAuditStorage
)

logger = logging.getLogger(__name__)

class VisibilityAudit:
    """Visibility audit logging"""
    
    def __init__(
        self,
        logger_name: str = "visibility.audit",
        storage: Optional[AuditStorage] = None
    ):
        self.logger = logging.getLogger(logger_name)
        self.setup_audit_logger()
        self.storage = storage or MongoAuditStorage()
    
    def setup_audit_logger(self) -> None:
        """Setup audit logger with custom formatting"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler for audit logs
        file_handler = logging.FileHandler('visibility_audit.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Set logging level
        self.logger.setLevel(logging.INFO)
    
    async def log_access_check(
        self,
        source: str,
        target: str,
        resource_type: str,
        allowed: bool,
        reason: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log access check event"""
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "access_check",
            "source": source,
            "target": target,
            "resource_type": resource_type,
            "allowed": allowed,
            "reason": reason,
            **kwargs
        }
        
        # Log to file
        self.logger.info(
            f"Access Check: {json.dumps(audit_data, default=str)}"
        )
        
        # Store in database
        await self.storage.store_event(
            event_type="access_check",
            event_data=audit_data
        )
    
    def log_visibility_change(
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
            old_state: Previous visibility state
            new_state: New visibility state
            change_type: Type of change
            **kwargs: Additional audit data
        """
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "visibility_change",
            "entity": entity,
            "old_state": old_state,
            "new_state": new_state,
            "change_type": change_type,
            **kwargs
        }
        
        self.logger.info(
            f"Visibility Change: {json.dumps(audit_data, default=str)}"
        )
    
    def log_rule_evaluation(
        self,
        rule_id: str,
        inputs: Dict[str, Any],
        result: bool,
        **kwargs
    ) -> None:
        """Log rule evaluation event
        
        Args:
            rule_id: Rule identifier
            inputs: Rule inputs
            result: Evaluation result
            **kwargs: Additional audit data
        """
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "rule_evaluation",
            "rule_id": rule_id,
            "inputs": inputs,
            "result": result,
            **kwargs
        }
        
        self.logger.info(
            f"Rule Evaluation: {json.dumps(audit_data, default=str)}"
        ) 