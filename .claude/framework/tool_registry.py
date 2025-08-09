"""Tool registry and management for agents."""

import asyncio
import inspect
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """Represents a tool that can be invoked by agents."""
    
    name: str
    handler: Callable[..., Any]
    required: bool = False
    description: str = ""
    parameters: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        """Post-initialization setup."""
        if self.parameters is None:
            # Extract parameters from handler signature
            self.parameters = self._extract_parameters()
    
    def _extract_parameters(self) -> Dict[str, Any]:
        """Extract parameter information from handler signature."""
        sig = inspect.signature(self.handler)
        params = {}
        
        for name, param in sig.parameters.items():
            if name in ["self", "cls"]:
                continue
            
            param_info = {
                "type": param.annotation if param.annotation != inspect.Parameter.empty else Any,
                "required": param.default == inspect.Parameter.empty,
            }
            
            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default
            
            params[name] = param_info
        
        return params


class ToolRegistry:
    """Registry for managing tools available to agents."""
    
    def __init__(self) -> None:
        """Initialize the tool registry."""
        self._tools: Dict[str, Tool] = {}
        self._required_tools: Set[str] = set()
        self._tool_chains: Dict[str, List[str]] = {}
        
        # Tool execution metrics
        self._execution_count: Dict[str, int] = {}
        self._error_count: Dict[str, int] = {}
    
    def register(
        self,
        name: str,
        handler: Callable[..., Any],
        required: bool = False,
        description: str = "",
    ) -> None:
        """Register a tool in the registry.
        
        Args:
            name: Tool name
            handler: Tool handler function
            required: Whether the tool is required
            description: Tool description
        """
        tool = Tool(
            name=name,
            handler=handler,
            required=required,
            description=description,
        )
        
        self._tools[name] = tool
        
        if required:
            self._required_tools.add(name)
        
        logger.debug(f"Registered tool: {name} (required: {required})")
    
    def unregister(self, name: str) -> None:
        """Unregister a tool from the registry.
        
        Args:
            name: Tool name
        """
        if name in self._tools:
            del self._tools[name]
            self._required_tools.discard(name)
            logger.debug(f"Unregistered tool: {name}")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None
        """
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def get_required_tools(self) -> Set[str]:
        """Get set of required tool names.
        
        Returns:
            Set of required tool names
        """
        return self._required_tools.copy()
    
    def validate_required_tools(self) -> bool:
        """Validate that all required tools are registered.
        
        Returns:
            True if all required tools are registered
            
        Raises:
            ValueError: If required tools are missing
        """
        missing = self._required_tools - set(self._tools.keys())
        if missing:
            raise ValueError(f"Missing required tools: {missing}")
        return True
    
    async def invoke(
        self,
        name: str,
        **kwargs: Any,
    ) -> Any:
        """Invoke a tool by name.
        
        Args:
            name: Tool name
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool not found
            TypeError: If invalid parameters
        """
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        
        # Validate parameters
        self._validate_parameters(tool, kwargs)
        
        # Update metrics
        self._execution_count[name] = self._execution_count.get(name, 0) + 1
        
        try:
            # Execute tool
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**kwargs)
            else:
                result = tool.handler(**kwargs)
            
            logger.debug(f"Tool {name} executed successfully")
            return result
            
        except Exception as e:
            self._error_count[name] = self._error_count.get(name, 0) + 1
            logger.error(f"Tool {name} execution failed: {e}")
            raise
    
    def _validate_parameters(self, tool: Tool, params: Dict[str, Any]) -> None:
        """Validate tool parameters.
        
        Args:
            tool: Tool instance
            params: Provided parameters
            
        Raises:
            TypeError: If parameters are invalid
        """
        # Check for required parameters
        for param_name, param_info in tool.parameters.items():
            if param_info.get("required", False) and param_name not in params:
                raise TypeError(f"Tool {tool.name} missing required parameter: {param_name}")
        
        # Check for unknown parameters
        known_params = set(tool.parameters.keys())
        provided_params = set(params.keys())
        unknown = provided_params - known_params
        
        if unknown:
            logger.warning(f"Tool {tool.name} received unknown parameters: {unknown}")
    
    def create_chain(self, name: str, tool_names: List[str]) -> None:
        """Create a tool chain for sequential execution.
        
        Args:
            name: Chain name
            tool_names: List of tool names in execution order
        """
        # Validate all tools exist
        for tool_name in tool_names:
            if tool_name not in self._tools:
                raise ValueError(f"Tool not found for chain: {tool_name}")
        
        self._tool_chains[name] = tool_names
        logger.debug(f"Created tool chain {name}: {tool_names}")
    
    async def invoke_chain(
        self,
        name: str,
        initial_params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Invoke a tool chain.
        
        Args:
            name: Chain name
            initial_params: Initial parameters for first tool
            
        Returns:
            Final result from chain execution
        """
        if name not in self._tool_chains:
            raise ValueError(f"Tool chain not found: {name}")
        
        tool_names = self._tool_chains[name]
        result = initial_params or {}
        
        for tool_name in tool_names:
            # Pass result from previous tool as input to next
            if isinstance(result, dict):
                result = await self.invoke(tool_name, **result)
            else:
                result = await self.invoke(tool_name, input=result)
        
        return result
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get tool execution metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "tools_registered": len(self._tools),
            "required_tools": len(self._required_tools),
            "chains_defined": len(self._tool_chains),
            "execution_count": self._execution_count.copy(),
            "error_count": self._error_count.copy(),
        }
    
    def reset_metrics(self) -> None:
        """Reset execution metrics."""
        self._execution_count.clear()
        self._error_count.clear()


# Standard tool implementations
class StandardTools:
    """Collection of standard tools for agents."""
    
    @staticmethod
    async def file_reader(filepath: str, encoding: str = "utf-8") -> str:
        """Read file contents.
        
        Args:
            filepath: Path to file
            encoding: File encoding
            
        Returns:
            File contents
        """
        from pathlib import Path
        return Path(filepath).read_text(encoding=encoding)
    
    @staticmethod
    async def file_writer(filepath: str, content: str, encoding: str = "utf-8") -> None:
        """Write content to file.
        
        Args:
            filepath: Path to file
            content: Content to write
            encoding: File encoding
        """
        from pathlib import Path
        Path(filepath).write_text(content, encoding=encoding)
    
    @staticmethod
    async def shell_command(command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute shell command.
        
        Args:
            command: Command to execute
            timeout: Execution timeout in seconds
            
        Returns:
            Command result with stdout, stderr, and return code
        """
        import subprocess
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "returncode": -1,
            }
    
    @staticmethod
    async def http_request(
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request.
        
        Args:
            url: Request URL
            method: HTTP method
            headers: Request headers
            data: Request data
            
        Returns:
            Response data
        """
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data if method in ["POST", "PUT", "PATCH"] else None,
                )
                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content": response.text,
                }
        except ImportError:
            return {
                "error": "httpx not installed",
                "status_code": -1,
                "content": "",
            }


def create_standard_registry() -> ToolRegistry:
    """Create a tool registry with standard tools.
    
    Returns:
        ToolRegistry with standard tools registered
    """
    registry = ToolRegistry()
    
    # Register standard tools
    registry.register(
        "file_reader",
        StandardTools.file_reader,
        description="Read file contents",
    )
    registry.register(
        "file_writer",
        StandardTools.file_writer,
        description="Write content to file",
    )
    registry.register(
        "shell_command",
        StandardTools.shell_command,
        description="Execute shell command",
    )
    registry.register(
        "http_request",
        StandardTools.http_request,
        description="Make HTTP request",
    )
    
    return registry