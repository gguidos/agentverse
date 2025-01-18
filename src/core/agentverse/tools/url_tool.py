"""
URL handling and validation tool
"""

import logging
from typing import Optional, ClassVar, List
import validators
import httpx
from pydantic import BaseModel, Field
from src.core.agentverse.tools.types import AgentCapability, ToolType
from src.core.agentverse.tools.registry import tool_registry
from src.core.agentverse.exceptions import ToolError
from src.core.agentverse.tools.base import BaseTool, ToolConfig

logger = logging.getLogger(__name__)
    
class URLToolConfig(ToolConfig):
    """Configuration for URL tool"""
    timeout: float = 10.0
    max_size: int = 1024 * 1024  # 1MB
    user_agent: str = "AgentVerse/1.0"
    follow_redirects: bool = True


@tool_registry.register(AgentCapability.URL, ToolType.SIMPLE)
class URLTool(BaseTool):
    name: ClassVar[str] = "url"
    description: ClassVar[str] = "Tool for URL validation and fetching"
    version: ClassVar[str] = "1.0.0"
    capabilities: ClassVar[List[str]] = [AgentCapability.URL]
    
    def __init__(self, config: Optional[URLToolConfig] = None):
        super().__init__(config=config or URLToolConfig())
        self.client = httpx.AsyncClient(
            timeout=self.config.timeout,
            follow_redirects=self.config.follow_redirects,
            headers={"User-Agent": self.config.user_agent}
        )
    
    async def validate_url(self, url: str) -> bool:
        """Validate URL format
        
        Args:
            url: URL to validate
            
        Returns:
            Whether URL is valid
        """
        return bool(validators.url(url))
    
    async def fetch_url(self, url: str) -> str:
        """Fetch URL content
        
        Args:
            url: URL to fetch
            
        Returns:
            URL content
            
        Raises:
            ToolError: If fetch fails
        """
        try:
            # Validate URL
            if not await self.validate_url(url):
                raise ToolError(
                    message="Invalid URL format",
                    details={"url": url}
                )
            
            # Fetch content
            async with self.client.stream("GET", url) as response:
                response.raise_for_status()
                
                # Check content size
                content_length = int(response.headers.get("content-length", 0))
                if content_length > self.config.max_size:
                    raise ToolError(
                        message="Content too large",
                        details={
                            "url": url,
                            "size": content_length,
                            "max_size": self.config.max_size
                        }
                    )
                
                return await response.text()
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching URL {url}: {e}")
            raise ToolError(
                message="Failed to fetch URL",
                details={
                    "url": url,
                    "error": str(e)
                }
            )
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
            raise ToolError(
                message="URL fetch failed",
                details={
                    "url": url,
                    "error": str(e)
                }
            )
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose() 