from typing import Dict, Any, ClassVar, Optional, List
import logging
from urllib.parse import urlparse, urljoin, quote, unquote, parse_qs, urlencode
import validators
import tldextract
from datetime import datetime

from src.core.agentverse.tools.base import BaseTool, ToolResult, ToolConfig, ToolExecutionError

logger = logging.getLogger(__name__)

class URLToolConfig(ToolConfig):
    """URL tool specific configuration"""
    max_url_length: int = 2048  # Standard max URL length
    allowed_schemes: List[str] = ["http", "https"]
    validate_tld: bool = True
    normalize_urls: bool = True
    track_usage: bool = True

class URLTool(BaseTool):
    """Tool for URL operations and validation"""
    
    name: ClassVar[str] = "url"
    description: ClassVar[str] = """
    Handle URL operations like parsing, joining, encoding/decoding, and validation.
    Supports URL normalization, query parameter handling, and domain extraction.
    """
    version: ClassVar[str] = "1.1.0"
    parameters: ClassVar[Dict[str, Any]] = {
        "operation": {
            "type": "string",
            "description": "The URL operation to perform",
            "required": True,
            "enum": [
                "parse", "join", "encode", "decode", "validate",
                "normalize", "get_domain", "query_params", "build"
            ]
        },
        "url": {
            "type": "string",
            "description": "The URL to process",
            "required": True
        },
        "base_url": {
            "type": "string",
            "description": "Base URL for join operation",
            "required": False
        },
        "params": {
            "type": "object",
            "description": "Query parameters for build operation",
            "required": False
        }
    }
    required_permissions: ClassVar[List[str]] = ["url_access"]
    
    def __init__(self, config: Optional[URLToolConfig] = None):
        super().__init__(config=config or URLToolConfig())
    
    def _validate_url(self, url: str) -> Dict[str, Any]:
        """Validate URL and return detailed results"""
        try:
            parsed = urlparse(url)
            is_valid = validators.url(url)
            
            validation = {
                "is_valid": bool(is_valid),
                "scheme_valid": parsed.scheme in self.config.allowed_schemes,
                "length_valid": len(url) <= self.config.max_url_length,
                "has_domain": bool(parsed.netloc),
                "issues": []
            }
            
            if not validation["scheme_valid"]:
                validation["issues"].append(f"Invalid scheme: {parsed.scheme}")
            if not validation["length_valid"]:
                validation["issues"].append("URL exceeds maximum length")
            if not validation["has_domain"]:
                validation["issues"].append("Missing domain")
                
            if self.config.validate_tld:
                ext = tldextract.extract(url)
                validation["tld_valid"] = bool(ext.suffix)
                if not validation["tld_valid"]:
                    validation["issues"].append("Invalid top-level domain")
            
            return validation
            
        except Exception as e:
            logger.error(f"URL validation error: {str(e)}")
            return {
                "is_valid": False,
                "issues": [str(e)]
            }
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL format"""
        try:
            parsed = urlparse(url)
            # Ensure scheme
            if not parsed.scheme:
                url = f"https://{url}"
                parsed = urlparse(url)
            
            # Remove default ports
            netloc = parsed.netloc
            if ":80" in netloc and parsed.scheme == "http":
                netloc = netloc.replace(":80", "")
            elif ":443" in netloc and parsed.scheme == "https":
                netloc = netloc.replace(":443", "")
            
            # Normalize path
            path = parsed.path
            if not path:
                path = "/"
            
            # Sort query parameters
            query = parse_qs(parsed.query)
            sorted_query = urlencode(sorted(query.items()), doseq=True)
            
            # Remove trailing slash if no path
            if path == "/" and not sorted_query and not parsed.fragment:
                path = ""
            
            return parsed._replace(
                scheme=parsed.scheme.lower(),
                netloc=netloc.lower(),
                path=path,
                query=sorted_query
            ).geturl()
            
        except Exception as e:
            logger.error(f"URL normalization error: {str(e)}")
            raise ToolExecutionError(f"Failed to normalize URL: {str(e)}", e)
    
    async def execute(
        self,
        operation: str,
        url: str,
        base_url: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """Execute URL operations"""
        try:
            # Normalize URL if configured
            if self.config.normalize_urls and operation != "normalize":
                url = self._normalize_url(url)
            
            if operation == "parse":
                parsed = urlparse(url)
                ext = tldextract.extract(url)
                
                return ToolResult(
                    success=True,
                    result={
                        "scheme": parsed.scheme,
                        "netloc": parsed.netloc,
                        "path": parsed.path,
                        "params": parsed.params,
                        "query": parse_qs(parsed.query),
                        "fragment": parsed.fragment,
                        "domain": {
                            "subdomain": ext.subdomain,
                            "domain": ext.domain,
                            "suffix": ext.suffix
                        }
                    },
                    metadata={"original_url": url}
                )
                
            elif operation == "join":
                if not base_url:
                    raise ValueError("base_url is required for join operation")
                    
                joined = urljoin(base_url, url)
                return ToolResult(
                    success=True,
                    result=joined,
                    metadata={
                        "base_url": base_url,
                        "relative_url": url
                    }
                )
                
            elif operation == "encode":
                encoded = quote(url, safe=":/?=&")
                return ToolResult(
                    success=True,
                    result=encoded,
                    metadata={
                        "original_length": len(url),
                        "encoded_length": len(encoded)
                    }
                )
                
            elif operation == "decode":
                decoded = unquote(url)
                return ToolResult(
                    success=True,
                    result=decoded,
                    metadata={
                        "original_length": len(url),
                        "decoded_length": len(decoded)
                    }
                )
                
            elif operation == "validate":
                validation = self._validate_url(url)
                return ToolResult(
                    success=True,
                    result=validation,
                    metadata={"url": url}
                )
                
            elif operation == "normalize":
                normalized = self._normalize_url(url)
                return ToolResult(
                    success=True,
                    result=normalized,
                    metadata={
                        "original_url": url,
                        "changes": normalized != url
                    }
                )
                
            elif operation == "get_domain":
                ext = tldextract.extract(url)
                return ToolResult(
                    success=True,
                    result={
                        "subdomain": ext.subdomain,
                        "domain": ext.domain,
                        "suffix": ext.suffix,
                        "fqdn": ext.fqdn,
                        "registered_domain": ext.registered_domain
                    }
                )
                
            elif operation == "query_params":
                parsed = urlparse(url)
                params = parse_qs(parsed.query)
                return ToolResult(
                    success=True,
                    result=params,
                    metadata={
                        "param_count": len(params),
                        "has_params": bool(params)
                    }
                )
                
            elif operation == "build":
                if not params:
                    raise ValueError("params is required for build operation")
                    
                parsed = urlparse(url)
                query = urlencode(params, doseq=True)
                built = parsed._replace(query=query).geturl()
                
                return ToolResult(
                    success=True,
                    result=built,
                    metadata={
                        "original_url": url,
                        "added_params": list(params.keys())
                    }
                )
                
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"URL operation error: {str(e)}")
            raise ToolExecutionError(f"URL operation failed: {str(e)}", e) 