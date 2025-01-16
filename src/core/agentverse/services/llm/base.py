from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class LLMConfig(BaseModel):
    """LLM service configuration"""
    model: str
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 30

class LLMResponse(BaseModel):
    """LLM response"""
    text: str
    usage: Dict[str, int]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseLLMService(ABC):
    """Base class for LLM services"""
    
    def __init__(self, config: LLMConfig):
        """Initialize LLM service
        
        Args:
            config: Service configuration
        """
        self.config = config
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> LLMResponse:
        """Generate text completion
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated response
            
        Raises:
            LLMError: If generation fails
        """
        pass
    
    @abstractmethod
    async def get_embeddings(
        self,
        text: Union[str, List[str]],
        **kwargs
    ) -> Union[List[float], List[List[float]]]:
        """Get text embeddings
        
        Args:
            text: Input text(s)
            **kwargs: Additional parameters
            
        Returns:
            Text embedding(s)
            
        Raises:
            LLMError: If embedding fails
        """
        pass
    
    @abstractmethod
    async def evaluate(
        self,
        input: str,
        output: str,
        criteria: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, float]:
        """Evaluate text against criteria
        
        Args:
            input: Input text
            output: Output text
            criteria: Evaluation criteria
            **kwargs: Additional parameters
            
        Returns:
            Evaluation scores
            
        Raises:
            LLMError: If evaluation fails
        """
        pass
    
    async def _validate_input(
        self,
        text: Union[str, List[str]]
    ) -> None:
        """Validate input text
        
        Args:
            text: Input text to validate
            
        Raises:
            ValueError: If input is invalid
        """
        if isinstance(text, str) and not text.strip():
            raise ValueError("Empty input text")
        elif isinstance(text, list) and not all(t.strip() for t in text):
            raise ValueError("Empty text in list") 