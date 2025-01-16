from typing import Optional, Dict, Any
from datetime import datetime

class EnvironmentError(Exception):
    """Base class for environment-related exceptions"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        environment_id: Optional[str] = None
    ):
        self.message = message
        self.details = details or {}
        self.environment_id = environment_id
        self.timestamp = datetime.utcnow()
        
        # Build error message
        error_msg = f"Environment error: {message}"
        if environment_id:
            error_msg += f" (environment: {environment_id})"
        if details:
            error_msg += f"\nDetails: {details}"
            
        super().__init__(error_msg)

class RuleValidationError(EnvironmentError):
    """Raised when a rule validation fails"""
    
    def __init__(
        self,
        message: str,
        rule_name: str,
        validation_details: Dict[str, Any],
        **kwargs
    ):
        details = {
            "rule_name": rule_name,
            "validation": validation_details,
            **kwargs.get("details", {})
        }
        super().__init__(
            message=f"Rule validation failed: {message}",
            details=details,
            **kwargs
        )

class StateError(EnvironmentError):
    """Raised when there's an issue with the environment state"""
    
    def __init__(
        self,
        message: str,
        state_details: Dict[str, Any],
        **kwargs
    ):
        details = {
            "state": state_details,
            "status": state_details.get("status"),
            **kwargs.get("details", {})
        }
        super().__init__(
            message=f"State error: {message}",
            details=details,
            **kwargs
        )

class ActionError(EnvironmentError):
    """Raised when an invalid action is attempted"""
    
    def __init__(
        self,
        message: str,
        action: str,
        agent_id: Optional[str] = None,
        **kwargs
    ):
        details = {
            "action": action,
            "agent_id": agent_id,
            **kwargs.get("details", {})
        }
        super().__init__(
            message=f"Invalid action: {message}",
            details=details,
            **kwargs
        )

class AgentError(EnvironmentError):
    """Raised when there's an issue with an agent"""
    
    def __init__(
        self,
        message: str,
        agent_id: str,
        agent_type: Optional[str] = None,
        **kwargs
    ):
        details = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            **kwargs.get("details", {})
        }
        super().__init__(
            message=f"Agent error: {message}",
            details=details,
            **kwargs
        )

class MessageError(EnvironmentError):
    """Raised when there's an issue with message processing"""
    
    def __init__(
        self,
        message: str,
        message_id: Optional[str] = None,
        sender: Optional[str] = None,
        **kwargs
    ):
        details = {
            "message_id": message_id,
            "sender": sender,
            **kwargs.get("details", {})
        }
        super().__init__(
            message=f"Message error: {message}",
            details=details,
            **kwargs
        )

class EvaluationError(EnvironmentError):
    """Raised when there's an issue with evaluation"""
    
    def __init__(
        self,
        message: str,
        evaluator_id: Optional[str] = None,
        metrics: Optional[Dict[str, float]] = None,
        **kwargs
    ):
        details = {
            "evaluator_id": evaluator_id,
            "metrics": metrics,
            **kwargs.get("details", {})
        }
        super().__init__(
            message=f"Evaluation error: {message}",
            details=details,
            **kwargs
        )

class ConcurrencyError(EnvironmentError):
    """Raised when there's an issue with concurrent operations"""
    
    def __init__(
        self,
        message: str,
        operation: str,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        details = {
            "operation": operation,
            "resource_id": resource_id,
            **kwargs.get("details", {})
        }
        super().__init__(
            message=f"Concurrency error: {message}",
            details=details,
            **kwargs
        )

class ConfigurationError(EnvironmentError):
    """Raised when there's an issue with environment configuration"""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Any = None,
        **kwargs
    ):
        details = {
            "config_key": config_key,
            "config_value": config_value,
            **kwargs.get("details", {})
        }
        super().__init__(
            message=f"Configuration error: {message}",
            details=details,
            **kwargs
        ) 