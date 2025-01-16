"""Base Describer Module"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel

class DescriberConfig(BaseModel):
    """Describer configuration"""
    format: str = "markdown"
    include_examples: bool = True
    max_depth: int = 3
    language: str = "en"

class BaseDescriber(ABC):
    """Base class for describers"""
    
    def __init__(self, config: Optional[DescriberConfig] = None):
        self.config = config or DescriberConfig()
    
    @abstractmethod
    async def describe(self, **kwargs) -> str:
        """Generate description"""
        pass
    
    @abstractmethod
    async def generate_schema(self, **kwargs) -> Dict[str, Any]:
        """Generate schema documentation"""
        pass 