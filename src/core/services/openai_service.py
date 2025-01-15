from typing import List, Dict, Any
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self, api_key: str, system_prompt: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.system_prompt = system_prompt

    async def generate_response(self, 
                              messages: List[Dict[str, str]], 
                              temperature: float = 0.7,
                              max_tokens: int = 150) -> str:
        """Generate response using OpenAI API"""
        try:
            # Add system prompt to messages
            full_messages = [
                {"role": "system", "content": self.system_prompt}
            ] + messages

            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise