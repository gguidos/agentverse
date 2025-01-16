"""
Database repository module
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

class DBConfig(BaseModel):
    """Database configuration"""
    
    host: str = Field(description="Database host")
    port: int = Field(description="Database port")
    username: str = Field(description="Database username")
    password: str = Field(description="Database password")
    database: str = Field(description="Database name")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "host": "localhost",
                "port": 5432,
                "username": "postgres",
                "password": "secret",
                "database": "agentverse"
            }]
        }
    }

class DBRecord(BaseModel):
    """Database record model"""
    
    id: str = Field(description="Record ID")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "id": "rec_123",
                "data": {
                    "name": "Test Record",
                    "value": 42
                }
            }]
        }
    }

class DBRepository:
    """Database repository implementation"""
    
    def __init__(self, config: DBConfig):
        self.config = config
        self._records: Dict[str, DBRecord] = {}
    
    async def get(self, record_id: str) -> Optional[DBRecord]:
        """Get record by ID"""
        return self._records.get(record_id)
    
    async def create(self, record: DBRecord) -> DBRecord:
        """Create new record"""
        self._records[record.id] = record
        return record
    
    async def update(self, record: DBRecord) -> DBRecord:
        """Update existing record"""
        record.updated_at = datetime.now()
        self._records[record.id] = record
        return record
    
    async def delete(self, record_id: str) -> None:
        """Delete record by ID"""
        self._records.pop(record_id, None)
    
    async def list(self) -> List[DBRecord]:
        """List all records"""
        return list(self._records.values())

__all__ = [
    "DBConfig",
    "DBRecord",
    "DBRepository"
]
