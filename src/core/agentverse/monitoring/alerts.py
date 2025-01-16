"""Alert Management Module"""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import logging
import uuid

logger = logging.getLogger(__name__)

class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class Alert(BaseModel):
    """Alert definition"""
    id: str
    level: AlertLevel
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AlertManager:
    """Alert management system"""
    
    @classmethod
    async def send_alert(
        cls,
        level: Union[str, AlertLevel],
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Send new alert"""
        # Create alert
        alert = Alert(
            id=str(uuid.uuid4()),
            level=AlertLevel(level),
            message=message,
            details=details or {}
        )
        
        # Log alert
        log_level = logging.WARNING if alert.level in (
            AlertLevel.WARNING,
            AlertLevel.ERROR,
            AlertLevel.CRITICAL
        ) else logging.INFO
        
        logger.log(
            log_level,
            f"Alert [{alert.level}]: {alert.message}"
        )
        
        return alert 