import os
import json
import yaml
from typing import Dict, Any, ClassVar, List, Optional
from pathlib import Path
import mimetypes
import logging
from datetime import datetime
from src.core.agentverse.tools.registry import tool_registry
from src.core.agentverse.tools.types import AgentCapability, ToolType

from src.core.agentverse.tools.base import (
    BaseTool, 
    ToolResult, 
    ToolConfig, 
    ToolExecutionError,
    ToolAuthenticationError
)

logger = logging.getLogger(__name__)

class FileToolConfig(ToolConfig):
    """File tool specific configuration"""
    root_dir: str = "/app/data"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: List[str] = ["txt", "json", "yaml", "yml", "md"]
    create_dirs: bool = True
    backup_files: bool = True
    requires_auth: bool = True

@tool_registry.register(AgentCapability.FILE, ToolType.SIMPLE)
class FileTool(BaseTool):
    """Tool for file operations"""
    
    name: ClassVar[str] = "file"
    description: ClassVar[str] = """
    Handle file operations like reading, writing, listing, and getting file information.
    Supports various file formats and provides safe file operations.
    """
    version: ClassVar[str] = "1.1.0"
    parameters: ClassVar[Dict[str, Any]] = {
        "operation": {
            "type": "string",
            "description": "The file operation to perform",
            "required": True,
            "enum": ["read", "write", "list", "info", "exists", "delete", "move"]
        },
        "path": {
            "type": "string",
            "description": "File or directory path",
            "required": True
        },
        "content": {
            "type": "string",
            "description": "Content to write (for write operation)",
            "required": False
        },
        "format": {
            "type": "string",
            "description": "File format for reading/writing",
            "enum": ["text", "json", "yaml"],
            "default": "text",
            "required": False
        },
        "target_path": {
            "type": "string",
            "description": "Target path for move operation",
            "required": False
        }
    }
    required_permissions: ClassVar[List[str]] = ["file_access"]
    
    def __init__(self, config: Optional[FileToolConfig] = None):
        super().__init__(config=config or FileToolConfig())
        
    def _ensure_safe_path(self, path: str) -> Path:
        """Ensure path is within allowed directory and has valid extension"""
        try:
            # Convert to Path object and resolve
            full_path = Path(self.config.root_dir) / path
            safe_path = full_path.resolve()
            
            # Check if path is within root directory
            if not str(safe_path).startswith(str(Path(self.config.root_dir).resolve())):
                raise ValueError("Access denied: Path outside allowed directory")
            
            # Check file extension
            if safe_path.suffix:
                ext = safe_path.suffix[1:].lower()
                if ext not in self.config.allowed_extensions:
                    raise ValueError(f"Unsupported file extension: {ext}")
                    
            return safe_path
            
        except Exception as e:
            logger.error(f"Path validation error: {str(e)}")
            raise ToolExecutionError(f"Invalid path: {str(e)}", e)
    
    async def execute(
        self,
        operation: str,
        path: str,
        content: Optional[str] = None,
        format: str = "text",
        target_path: Optional[str] = None
    ) -> ToolResult:
        """Execute file operations"""
        try:
            safe_path = self._ensure_safe_path(path)
            
            if operation == "read":
                return await self._read_file(safe_path, format)
                
            elif operation == "write":
                return await self._write_file(safe_path, content, format)
                
            elif operation == "list":
                return await self._list_directory(safe_path)
                
            elif operation == "info":
                return await self._get_file_info(safe_path)
                
            elif operation == "exists":
                return ToolResult(
                    success=True,
                    result=safe_path.exists(),
                    metadata={"path": str(safe_path)}
                )
                
            elif operation == "delete":
                return await self._delete_file(safe_path)
                
            elif operation == "move":
                if not target_path:
                    raise ValueError("target_path is required for move operation")
                safe_target = self._ensure_safe_path(target_path)
                return await self._move_file(safe_path, safe_target)
                
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"File operation error: {str(e)}")
            raise ToolExecutionError(f"File operation failed: {str(e)}", e)
    
    async def _read_file(self, path: Path, format: str) -> ToolResult:
        """Read file content"""
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
            
        if path.stat().st_size > self.config.max_file_size:
            raise ValueError(f"File too large: {path}")
            
        content = path.read_text()
        if format == "json":
            content = json.loads(content)
        elif format == "yaml":
            content = yaml.safe_load(content)
            
        return ToolResult(
            success=True,
            result=content,
            metadata={
                "format": format,
                "size": path.stat().st_size,
                "path": str(path)
            }
        )
    
    async def _write_file(self, path: Path, content: str, format: str) -> ToolResult:
        """Write content to file"""
        if not content:
            raise ValueError("Content is required for write operation")
            
        # Create parent directories if needed
        if self.config.create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
            
        # Backup existing file if enabled
        if self.config.backup_files and path.exists():
            backup_path = path.with_suffix(f"{path.suffix}.bak")
            path.rename(backup_path)
            
        # Format content
        if format == "json":
            content = json.dumps(content, indent=2)
        elif format == "yaml":
            content = yaml.dump(content)
            
        # Write file
        path.write_text(content)
        
        return ToolResult(
            success=True,
            result=f"File written successfully: {path}",
            metadata={
                "size": path.stat().st_size,
                "path": str(path)
            }
        )
    
    async def _list_directory(self, path: Path) -> ToolResult:
        """List directory contents"""
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
            
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")
            
        entries = []
        for entry in path.iterdir():
            stat = entry.stat()
            entries.append({
                "name": entry.name,
                "type": "file" if entry.is_file() else "directory",
                "size": stat.st_size if entry.is_file() else None,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "extension": entry.suffix[1:] if entry.suffix else None
            })
            
        return ToolResult(
            success=True,
            result=entries,
            metadata={
                "count": len(entries),
                "path": str(path)
            }
        )
    
    async def _get_file_info(self, path: Path) -> ToolResult:
        """Get file information"""
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
            
        stat = path.stat()
        mime_type, _ = mimetypes.guess_type(str(path))
        
        return ToolResult(
            success=True,
            result={
                "name": path.name,
                "extension": path.suffix[1:] if path.suffix else None,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "type": mime_type or "unknown",
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
                "permissions": oct(stat.st_mode)[-3:]
            },
            metadata={"path": str(path)}
        )
    
    async def _delete_file(self, path: Path) -> ToolResult:
        """Delete file or directory"""
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
            
        if path.is_file():
            path.unlink()
        else:
            path.rmdir()  # Only removes empty directories
            
        return ToolResult(
            success=True,
            result=f"Successfully deleted: {path}",
            metadata={"path": str(path)}
        )
    
    async def _move_file(self, source: Path, target: Path) -> ToolResult:
        """Move file to new location"""
        if not source.exists():
            raise FileNotFoundError(f"Source not found: {source}")
            
        if target.exists():
            raise FileExistsError(f"Target already exists: {target}")
            
        source.rename(target)
        
        return ToolResult(
            success=True,
            result=f"Successfully moved {source} to {target}",
            metadata={
                "source": str(source),
                "target": str(target)
            }
        ) 