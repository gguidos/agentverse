from abc import abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class LLMResult(BaseModel):
    """Standard result format for LLM responses"""
    content: str
    raw_response: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "arbitrary_types_allowed": True,
        "ser_json_timedelta": "iso8601"
    }

class LLMConfig(BaseModel):
    """Base configuration for LLM models"""
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    max_retries: int = 3

class BaseLLM(BaseModel):
    """Base class for LLM implementations"""
    
    config: LLMConfig = Field(default_factory=LLMConfig)
    
    model_config = {
        "arbitrary_types_allowed": True
    }

    @abstractmethod
    async def generate_response(self, prompt: str) -> LLMResult:
        """Generate a response from the LLM"""
        raise NotImplementedError()

class BaseChatModel(BaseLLM):
    """Base class for chat-based models (e.g., GPT-3.5, GPT-4)"""
    
    async def generate_response(self,
                              prompt: str = None,
                              messages: List[Dict] = None,
                              **kwargs) -> LLMResult:
        """Generate response from chat messages"""
        if not messages:
            messages = [{"role": "user", "content": prompt}]
            
        return await self._chat_completion(messages, **kwargs)
    
    @abstractmethod
    async def _chat_completion(self,
                             messages: List[Dict],
                             **kwargs) -> LLMResult:
        """Implement specific chat completion logic"""
        pass

class BaseCompletionModel(BaseLLM):
    """Base class for completion-based models (e.g., text-davinci)"""
    
    async def generate_response(self,
                              prompt: str,
                              **kwargs) -> LLMResult:
        """Generate completion from prompt"""
        return await self._text_completion(prompt, **kwargs)
    
    @abstractmethod
    async def _text_completion(self,
                             prompt: str,
                             **kwargs) -> LLMResult:
        """Implement specific text completion logic"""
        pass 