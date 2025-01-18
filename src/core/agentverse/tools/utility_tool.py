from typing import Dict, Any, ClassVar, Optional, List, Union
import logging
import ast
import math
import json
import yaml
from src.core.agentverse.tools.base import BaseTool, ToolResult, ToolConfig, ToolExecutionError
from src.core.agentverse.tools.types import AgentCapability, ToolType
from src.core.agentverse.tools.registry import tool_registry

logger = logging.getLogger(__name__)

class CalculateToolConfig(ToolConfig):
    """Calculate tool specific configuration"""
    max_expression_length: int = 1000
    enable_complex_math: bool = True
    decimal_precision: int = 6
    track_usage: bool = True

class FormatToolConfig(ToolConfig):
    """Format tool specific configuration"""
    max_data_size: int = 1024 * 1024  # 1MB
    pretty_print: bool = True
    max_table_rows: int = 1000
    track_usage: bool = True

@tool_registry.register(AgentCapability.CALCULATE, ToolType.SIMPLE)
class CalculateTool(BaseTool):
    """Tool for safe mathematical calculations"""
    
    name: ClassVar[str] = "calculate"
    description: ClassVar[str] = """
    Safely evaluate mathematical expressions with support for basic arithmetic,
    trigonometry, logarithms, and other common mathematical operations.
    """
    version: ClassVar[str] = "1.1.0"
    parameters: ClassVar[Dict[str, Any]] = {
        "expression": {
            "type": "string",
            "description": "Mathematical expression to evaluate",
            "required": True,
            "examples": ["2 + 2", "sqrt(16)", "sin(pi/2)"]
        },
        "precision": {
            "type": "integer",
            "description": "Decimal precision for result",
            "minimum": 1,
            "maximum": 15,
            "default": 6
        }
    }
    required_permissions: ClassVar[List[str]] = ["calculate_access"]
    
    # Safe math functions and constants
    SAFE_MATH_NAMES: ClassVar[Dict[str, Any]] = {
        # Basic math
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        
        # Advanced math
        'sqrt': math.sqrt,
        'pow': pow,
        'exp': math.exp,
        'log': math.log,
        'log10': math.log10,
        'log2': math.log2,
        
        # Trigonometry
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'asin': math.asin,
        'acos': math.acos,
        'atan': math.atan,
        'degrees': math.degrees,
        'radians': math.radians,
        
        # Constants
        'pi': math.pi,
        'e': math.e,
        'tau': math.tau,
        'inf': math.inf
    }
    
    def __init__(self, config: Optional[CalculateToolConfig] = None):
        super().__init__(config=config or CalculateToolConfig())
    
    def _validate_expression(self, expression: str) -> None:
        """Validate mathematical expression for safety"""
        if len(expression) > self.config.max_expression_length:
            raise ValueError(f"Expression too long (max {self.config.max_expression_length} chars)")
            
        # Parse into AST
        tree = ast.parse(expression, mode='eval')
        
        # Validate each node
        for node in ast.walk(tree):
            # Check for allowed operations
            if isinstance(node, ast.BinOp):
                if not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
                    raise ValueError(f"Invalid operation: {type(node.op).__name__}")
                    
            # Check for allowed functions/variables
            elif isinstance(node, ast.Name):
                if node.id not in self.SAFE_MATH_NAMES:
                    raise ValueError(f"Invalid function or variable: {node.id}")
                    
            # Prevent any other potentially unsafe operations
            elif not isinstance(node, (ast.Expression, ast.Num, ast.Call, ast.Load)):
                raise ValueError(f"Invalid expression element: {type(node).__name__}")
    
    async def execute(
        self,
        expression: str,
        precision: int = 6
    ) -> ToolResult:
        """Execute mathematical calculation"""
        try:
            # Validate expression
            self._validate_expression(expression)
            
            # Compile and evaluate
            code = compile(ast.parse(expression, mode='eval'), '<string>', 'eval')
            result = eval(code, {"__builtins__": {}}, self.SAFE_MATH_NAMES)
            
            # Format result
            if isinstance(result, (int, float)):
                result = round(result, min(precision, self.config.decimal_precision))
            
            return ToolResult(
                success=True,
                result=result,
                metadata={
                    "expression": expression,
                    "precision": precision,
                    "type": type(result).__name__
                }
            )
            
        except Exception as e:
            logger.error(f"Calculation error: {str(e)}")
            raise ToolExecutionError(f"Calculation failed: {str(e)}", e)

class FormatTool(BaseTool):
    """Tool for data formatting and conversion"""
    
    name: ClassVar[str] = "format"
    description: ClassVar[str] = """
    Format and convert data between different representations.
    Supports JSON, YAML, tables, and other common formats.
    """
    version: ClassVar[str] = "1.1.0"
    parameters: ClassVar[Dict[str, Any]] = {
        "data": {
            "type": "object",
            "description": "Data to format",
            "required": True
        },
        "format": {
            "type": "string",
            "description": "Output format",
            "required": True,
            "enum": ["json", "yaml", "table", "csv", "xml"]
        },
        "options": {
            "type": "object",
            "description": "Format-specific options",
            "required": False
        }
    }
    required_permissions: ClassVar[List[str]] = ["format_access"]
    
    def __init__(self, config: Optional[FormatToolConfig] = None):
        super().__init__(config=config or FormatToolConfig())
    
    def _validate_data_size(self, data: Union[Dict, List]) -> None:
        """Validate data size"""
        size = len(json.dumps(data))
        if size > self.config.max_data_size:
            raise ValueError(f"Data too large (max {self.config.max_data_size} bytes)")
    
    def _format_table(
        self,
        data: List[Dict],
        options: Dict[str, Any]
    ) -> str:
        """Format data as ASCII table"""
        if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
            raise ValueError("Table format requires list of dictionaries")
            
        if len(data) > self.config.max_table_rows:
            raise ValueError(f"Too many rows (max {self.config.max_table_rows})")
            
        # Get headers
        headers = list(data[0].keys())
        
        # Format rows
        rows = [[str(row.get(h, ""))[:50] for h in headers] for row in data]
        
        # Calculate column widths
        widths = [
            max(len(str(row[i])) for row in [headers] + rows)
            for i in range(len(headers))
        ]
        
        # Build table
        separator = "+".join("-" * (w + 2) for w in widths)
        result = [separator]
        
        # Add headers
        header_row = "|".join(
            f" {h:<{w}} " for h, w in zip(headers, widths)
        )
        result.extend([header_row, separator])
        
        # Add data rows
        for row in rows:
            result.append("|".join(
                f" {cell:<{w}} " for cell, w in zip(row, widths)
            ))
        result.append(separator)
        
        return "\n".join(result)
    
    async def execute(
        self,
        data: Union[Dict, List],
        format: str = "json",
        options: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """Execute data formatting"""
        try:
            # Validate data size
            self._validate_data_size(data)
            
            options = options or {}
            
            if format == "json":
                result = json.dumps(
                    data,
                    indent=2 if self.config.pretty_print else None,
                    sort_keys=options.get("sort_keys", True),
                    ensure_ascii=options.get("ensure_ascii", False)
                )
            
            elif format == "yaml":
                result = yaml.dump(
                    data,
                    default_flow_style=False,
                    sort_keys=options.get("sort_keys", True),
                    allow_unicode=True
                )
            
            elif format == "table":
                result = self._format_table(data, options)
            
            elif format == "csv":
                import csv
                from io import StringIO
                
                output = StringIO()
                if isinstance(data, list) and data:
                    writer = csv.DictWriter(output, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                result = output.getvalue()
                
            elif format == "xml":
                import dicttoxml
                result = dicttoxml.dicttoxml(
                    data,
                    custom_root=options.get("root", "root"),
                    attr_type=False
                ).decode()
                
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            return ToolResult(
                success=True,
                result=result,
                metadata={
                    "format": format,
                    "options": options,
                    "size": len(result)
                }
            )
            
        except Exception as e:
            logger.error(f"Formatting error: {str(e)}")
            raise ToolExecutionError(f"Formatting failed: {str(e)}", e) 