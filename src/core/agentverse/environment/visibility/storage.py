"""Visibility Audit Storage Module"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from src.core.repositories.db_repository import DBRepository
from src.core.infrastructure.db.mongo_client import MongoDBClient

logger = logging.getLogger(__name__)

class AuditStorage(ABC):
    """Base class for audit storage"""
    
    @abstractmethod
    async def store_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """Store audit event
        
        Args:
            event_type: Type of event
            event_data: Event data
        """
        pass
    
    @abstractmethod
    async def get_events(
        self,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        **filters
    ) -> List[Dict[str, Any]]:
        """Retrieve audit events
        
        Args:
            event_type: Optional event type filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            **filters: Additional filters
            
        Returns:
            List of matching events
        """
        pass

class MongoAuditStorage(AuditStorage):
    """MongoDB-based audit storage"""
    
    def __init__(self, collection_name: str = "audit_events"):
        self.mongo_client = MongoDBClient(collection_name)
        self.repository = DBRepository(self.mongo_client)
    
    async def store_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """Store audit event in MongoDB
        
        Args:
            event_type: Type of event
            event_data: Event data
        """
        try:
            audit_doc = {
                "timestamp": datetime.utcnow(),
                "event_type": event_type,
                **event_data
            }
            
            await self.repository.create(audit_doc)
            
        except Exception as e:
            logger.error(f"Failed to store audit event: {str(e)}")
            raise
    
    async def get_events(
        self,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        **filters
    ) -> List[Dict[str, Any]]:
        """Retrieve audit events from MongoDB
        
        Args:
            event_type: Optional event type filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            **filters: Additional filters
            
        Returns:
            List of matching events
        """
        try:
            # Build query
            query = {}
            
            if event_type:
                query["event_type"] = event_type
                
            if start_time or end_time:
                query["timestamp"] = {}
                if start_time:
                    query["timestamp"]["$gte"] = start_time
                if end_time:
                    query["timestamp"]["$lte"] = end_time
                    
            # Add additional filters
            query.update(filters)
            
            # Execute query
            events = await self.repository.find(query)
            return events
            
        except Exception as e:
            logger.error(f"Failed to retrieve audit events: {str(e)}")
            raise 