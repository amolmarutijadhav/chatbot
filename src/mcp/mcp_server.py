"""Abstract base class for MCP servers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from utils.logger import LoggerMixin
from utils.event_bus import publish_event


class MCPServer(ABC, LoggerMixin):
    """Abstract base class for MCP servers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the MCP server with configuration."""
        self.config = config
        self.name = config.get("name", "unknown")
        self.server_type = config.get("type", "unknown")
        self.transport_type = config.get("transport", "stdio")
        self.is_connected = False
        self.last_used = None
        self.request_count = 0
        self.error_count = 0
        self.capabilities = {}
        self.transport = None
        
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the MCP server."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the MCP server."""
        pass
    
    @abstractmethod
    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the MCP server."""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get server capabilities."""
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate the connection to the MCP server."""
        pass
    
    def update_usage_stats(self, success: bool = True):
        """Update usage statistics."""
        self.last_used = datetime.utcnow()
        self.request_count += 1
        if not success:
            self.error_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        return {
            "name": self.name,
            "type": self.server_type,
            "transport": self.transport_type,
            "is_connected": self.is_connected,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "success_rate": (self.request_count - self.error_count) / max(self.request_count, 1),
            "capabilities": self.capabilities
        }
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server-specific configuration."""
        return {
            "name": self.name,
            "type": self.server_type,
            "transport": self.transport_type,
            "config": self.config
        }
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool on the MCP server."""
        try:
            result = await self.send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })
            
            self.update_usage_stats(success=True)
            
            # Publish event
            publish_event("mcp_tool_called", {
                "server": self.name,
                "tool": tool_name,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return result
            
        except Exception as e:
            self.update_usage_stats(success=False)
            self.logger.error(f"Error calling tool '{tool_name}' on server '{self.name}': {e}")
            raise
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools on the MCP server."""
        try:
            result = await self.send_request("tools/list", {})
            return result.get("tools", [])
        except Exception as e:
            self.logger.error(f"Error listing tools on server '{self.name}': {e}")
            return []
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources on the MCP server."""
        try:
            result = await self.send_request("resources/list", {})
            return result.get("resources", [])
        except Exception as e:
            self.logger.error(f"Error listing resources on server '{self.name}': {e}")
            return []
    
    def has_capability(self, capability: str) -> bool:
        """Check if the server has a specific capability."""
        return capability in self.capabilities
    
    def get_capability_info(self, capability: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific capability."""
        return self.capabilities.get(capability)
    
    def __str__(self) -> str:
        return f"MCPServer(name={self.name}, type={self.server_type}, connected={self.is_connected})"
    
    def __repr__(self) -> str:
        return f"MCPServer(name='{self.name}', type='{self.server_type}', connected={self.is_connected})" 