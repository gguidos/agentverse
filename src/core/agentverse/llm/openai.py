import logging
from typing import List, Dict, Optional
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import AsyncOpenAI

from src.core.agentverse.llm.base import (
    BaseChatModel, 
    BaseCompletionModel, 
    LLMResult, 
    LLMConfig
)
from src.core.agentverse.llm.registry import llm_registry
from src.core.agentverse.memory.base import Message

logger = logging.getLogger(__name__)

class OpenAIConfig(LLMConfig):
    """OpenAI specific configuration"""
    api_type: str = "openai"  # or "azure"
    engine: str = "gpt-4-1106-preview"  # For Azure
    embedding_model: str = "text-embedding-ada-002"
    
    model_config = {
        "extra": "allow"
    }

@llm_registry.register("gpt-3.5-turbo", "gpt-4", "gpt-4-turbo")
class OpenAIChatModel(BaseChatModel):
    """OpenAI Chat Model Implementation"""
    
    def __init__(self, api_key: str, config: Optional[OpenAIConfig] = None):
        super().__init__(config=config or OpenAIConfig())
        self.client = AsyncOpenAI(api_key=api_key)
        
    def _construct_messages(self, 
                          prompt: str, 
                          chat_memory: Optional[List[Message]] = None,
                          system_prompt: Optional[str] = None) -> List[Dict]:
        """Construct messages for chat completion"""
        messages = []
        
        # Add system prompt
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
        # Add chat history
        if chat_memory:
            for msg in chat_memory:
                messages.append({
                    "role": "assistant" if msg.sender == "Assistant" else "user",
                    "content": msg.content
                })
                
        # Add current prompt
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        return messages
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _chat_completion(self,
                             messages: List[Dict],
                             **kwargs) -> LLMResult:
        """Generate chat completion using OpenAI API"""
        try:
            config_dict = self.config.model_dump(
                exclude={"api_type", "engine", "embedding_model"}
            )
            config_dict.update(kwargs)
            
            if self.config.api_type == "azure":
                response = await self.client.chat.completions.create(
                    engine=self.config.engine,
                    messages=messages,
                    **config_dict
                )
            else:
                response = await self.client.chat.completions.create(
                    messages=messages,
                    **config_dict
                )
                
            return LLMResult(
                content=response.choices[0].message.content,
                raw_response={
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise

@llm_registry.register("text-davinci-003")
class OpenAICompletionModel(BaseCompletionModel):
    """OpenAI Completion Model Implementation"""
    
    def __init__(self, api_key: str, config: Optional[OpenAIConfig] = None):
        super().__init__(config=config or OpenAIConfig())
        self.client = AsyncOpenAI(api_key=api_key)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _text_completion(self,
                             prompt: str,
                             **kwargs) -> LLMResult:
        """Generate text completion using OpenAI API"""
        try:
            config_dict = self.config.model_dump(
                exclude={"api_type", "engine", "embedding_model"}
            )
            config_dict.update(kwargs)
            
            response = await self.client.completions.create(
                prompt=prompt,
                **config_dict
            )
            
            return LLMResult(
                content=response.choices[0].text,
                raw_response={
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise

class OpenAIEmbedding:
    """OpenAI Embedding Service"""
    
    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using OpenAI API"""
        try:
            text = text.replace("\n", " ")
            response = await self.client.embeddings.create(
                input=[text],
                model=self.model
            )
            return np.array(response.data[0].embedding)
            
        except Exception as e:
            logger.error(f"Failed to get embedding: {str(e)}")
            raise 