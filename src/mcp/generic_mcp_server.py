"""Generic MCP server implementation."""

from typing import Dict, Any, Optional
from datetime import datetime

from .mcp_server import MCPServer
from .mcp_factory import MCPFactory
from utils.event_bus import publish_event


class GenericMCPServer(MCPServer):
    """Generic MCP server implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize generic MCP server."""
        super().__init__(config)
        self.transport = None
        
    async def connect(self) -> bool:
        """Connect to the MCP server."""
        try:
            # Create transport
            self.transport = MCPFactory.create_transport_from_config(self.config)
            
            # Connect transport
            if await self.transport.connect():
                self.is_connected = True
                
                # Get server capabilities
                await self.get_capabilities()
                
                self.logger.info(f"Connected to MCP server: {self.name}")
                
                # Publish event
                publish_event("mcp_server_connected", {
                    "server": self.name,
                    "type": self.server_type,
                    "transport": self.transport_type,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return True
            else:
                self.logger.error(f"Failed to connect transport for server: {self.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to MCP server '{self.name}': {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from the MCP server."""
        try:
            if self.transport:
                await self.transport.disconnect()
                self.transport = None
            
            self.is_connected = False
            self.logger.info(f"Disconnected from MCP server: {self.name}")
            
            # Publish event
            publish_event("mcp_server_disconnected", {
                "server": self.name,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from MCP server '{self.name}': {e}")
            return False
    
    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the MCP server."""
        if not self.is_connected or not self.transport:
            raise ConnectionError(f"MCP server '{self.name}' not connected")
        
        try:
            # Send request through transport
            response = await self.transport.send_request(method, params)
            
            # Update stats
            self.update_usage_stats(success=True)
            
            # Publish event
            publish_event("mcp_request_sent", {
                "server": self.name,
                "method": method,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return response
            
        except Exception as e:
            self.update_usage_stats(success=False)
            self.logger.error(f"Error sending request to MCP server '{self.name}': {e}")
            raise
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get server capabilities."""
        try:
            # Try to get capabilities from the server
            response = await self.send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "chatbot-framework",
                    "version": "1.0.0"
                }
            })
            
            # Extract capabilities from response
            if "result" in response:
                result = response["result"]
                self.capabilities = result.get("capabilities", {})
                return self.capabilities
            else:
                # Fallback to basic capabilities
                self.capabilities = {
                    "tools": {},
                    "resources": {},
                    "notifications": {}
                }
                return self.capabilities
                
        except Exception as e:
            self.logger.warning(f"Could not get capabilities from server '{self.name}': {e}")
            # Set basic capabilities
            self.capabilities = {
                "tools": {},
                "resources": {},
                "notifications": {}
            }
            return self.capabilities
    
    async def validate_connection(self) -> bool:
        """Validate the connection to the MCP server."""
        try:
            if not self.is_connected or not self.transport:
                return False
            
            # Try to send a simple request
            await self.send_request("tools/list", {})
            return True
            
        except Exception:
            return False
    
    async def list_tools(self) -> list[Dict[str, Any]]:
        """List available tools on the MCP server."""
        try:
            response = await self.send_request("tools/list", {})
            if "result" in response:
                return response["result"].get("tools", [])
            return []
        except Exception as e:
            self.logger.error(f"Error listing tools on server '{self.name}': {e}")
            return []
    
    async def list_resources(self) -> list[Dict[str, Any]]:
        """List available resources on the MCP server."""
        try:
            response = await self.send_request("resources/list", {})
            if "result" in response:
                return response["result"].get("resources", [])
            return []
        except Exception as e:
            self.logger.error(f"Error listing resources on server '{self.name}': {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool on the MCP server."""
        try:
            response = await self.send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })
            
            if "result" in response:
                return response["result"]
            else:
                raise Exception("No result in tool call response")
                
        except Exception as e:
            self.logger.error(f"Error calling tool '{tool_name}' on server '{self.name}': {e}")
            raise
    
    def get_transport_info(self) -> Dict[str, Any]:
        """Get information about the transport."""
        if not self.transport:
            return {}
        
        return {
            "type": self.transport_type,
            "connected": self.transport.is_connected,
            "config": self.transport.config
        } 