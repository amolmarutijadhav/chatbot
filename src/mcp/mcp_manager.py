"""Manager for MCP servers."""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from .mcp_server import MCPServer
from .mcp_factory import MCPFactory
from utils.logger import LoggerMixin
from utils.event_bus import publish_event


class MCPManager(LoggerMixin):
    """Manager for MCP servers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize MCP manager."""
        self.config = config
        self.servers: Dict[str, MCPServer] = {}
        self.health_check_interval = config.get("health_check_interval", 300)
        self.health_check_task: Optional[asyncio.Task] = None
        self.auto_discovery = config.get("auto_discovery", False)
        
    async def start(self):
        """Start the MCP manager."""
        try:
            # Initialize servers from config
            servers_config = self.config.get("servers", {})
            for server_name, server_config in servers_config.items():
                await self.add_server(server_name, server_config)
            
            # Start health check task
            if self.health_check_interval > 0:
                self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            self.logger.info(f"MCP Manager started with {len(self.servers)} servers")
            
            # Publish event
            publish_event("mcp_manager_started", {
                "servers_count": len(self.servers),
                "auto_discovery": self.auto_discovery,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Failed to start MCP Manager: {e}")
            raise
    
    async def stop(self):
        """Stop the MCP manager."""
        try:
            # Stop health check task
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Disconnect all servers
            for server in self.servers.values():
                await server.disconnect()
            
            self.servers.clear()
            self.logger.info("MCP Manager stopped")
            
            # Publish event
            publish_event("mcp_manager_stopped", {
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error stopping MCP Manager: {e}")
    
    async def add_server(self, name: str, config: Dict[str, Any]) -> bool:
        """Add a new MCP server."""
        try:
            # Validate config
            if not MCPFactory.validate_server_config(config):
                return False
            
            # Create server
            server = MCPFactory.create_mcp_server(config)
            
            # Connect server
            if await server.connect():
                self.servers[name] = server
                self.logger.info(f"Added MCP server: {name}")
                
                # Publish event
                publish_event("mcp_server_added", {
                    "server": name,
                    "type": server.server_type,
                    "transport": server.transport_type,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return True
            else:
                self.logger.error(f"Failed to connect server: {name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding server '{name}': {e}")
            return False
    
    async def remove_server(self, name: str) -> bool:
        """Remove an MCP server."""
        if name not in self.servers:
            return False
        
        try:
            server = self.servers[name]
            await server.disconnect()
            del self.servers[name]
            
            self.logger.info(f"Removed MCP server: {name}")
            
            # Publish event
            publish_event("mcp_server_removed", {
                "server": name,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing server '{name}': {e}")
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], server_name: Optional[str] = None) -> Dict[str, Any]:
        """Call a tool on an MCP server."""
        if not self.servers:
            raise RuntimeError("No MCP servers available")
        
        # Determine which server to use
        if server_name:
            if server_name not in self.servers:
                raise ValueError(f"Server '{server_name}' not found")
            servers_to_try = [server_name]
        else:
            servers_to_try = await self._find_servers_with_tool(tool_name)
        
        if not servers_to_try:
            raise ValueError(f"No servers found with tool '{tool_name}'")
        
        # Try servers in order
        last_error = None
        for server_name in servers_to_try:
            try:
                server = self.servers[server_name]
                
                # Check if server is connected
                if not server.is_connected:
                    if not await server.connect():
                        continue
                
                # Call tool
                result = await server.call_tool(tool_name, arguments)
                
                self.logger.info(f"Called tool '{tool_name}' on server: {server_name}")
                return result
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"Server '{server_name}' failed for tool '{tool_name}': {e}")
                
                # Try to reconnect server
                try:
                    await server.disconnect()
                    await server.connect()
                except Exception:
                    pass
                
                continue
        
        # All servers failed
        raise RuntimeError(f"All MCP servers failed for tool '{tool_name}'. Last error: {last_error}")
    
    async def _find_servers_with_tool(self, tool_name: str) -> List[str]:
        """Find servers that have a specific tool."""
        servers_with_tool = []
        
        for name, server in self.servers.items():
            # Check if server has the tool in its capabilities
            if server.has_capability("tools"):
                tools_info = await server.get_capability_info("tools")
                if tools_info and tool_name in tools_info:
                    servers_with_tool.append(name)
        
        return servers_with_tool
    
    async def get_server_stats(self) -> Dict[str, Any]:
        """Get statistics for all servers."""
        stats = {
            "total_servers": len(self.servers),
            "connected_servers": 0,
            "servers": {}
        }
        
        for name, server in self.servers.items():
            server_stats = server.get_stats()
            stats["servers"][name] = server_stats
            
            if server.is_connected:
                stats["connected_servers"] += 1
        
        return stats
    
    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on all servers."""
        health_status = {}
        
        for name, server in self.servers.items():
            try:
                is_healthy = await server.validate_connection()
                health_status[name] = is_healthy
                
                if not is_healthy and server.is_connected:
                    self.logger.warning(f"Server '{name}' health check failed")
                    await server.disconnect()
                    await server.connect()
                    
            except Exception as e:
                self.logger.error(f"Health check failed for server '{name}': {e}")
                health_status[name] = False
        
        return health_status
    
    async def _health_check_loop(self):
        """Background task for periodic health checks."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self.health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
    
    def get_server(self, name: str) -> Optional[MCPServer]:
        """Get a specific server by name."""
        return self.servers.get(name)
    
    def list_servers(self) -> List[str]:
        """Get list of all server names."""
        return list(self.servers.keys())
    
    def is_server_available(self, name: str) -> bool:
        """Check if a server is available and connected."""
        server = self.servers.get(name)
        return server is not None and server.is_connected
    
    async def discover_servers(self) -> List[Dict[str, Any]]:
        """Discover available MCP servers."""
        discovered_servers = []
        
        # This would implement server discovery logic
        # For now, return empty list
        self.logger.info("Server discovery not implemented yet")
        
        return discovered_servers
    
    async def get_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available tools from all servers."""
        all_tools = {}
        
        for name, server in self.servers.items():
            try:
                tools = await server.list_tools()
                if tools:
                    all_tools[name] = tools
            except Exception as e:
                self.logger.error(f"Error getting tools from server '{name}': {e}")
        
        return all_tools
    
    async def get_all_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available resources from all servers."""
        all_resources = {}
        
        for name, server in self.servers.items():
            try:
                resources = await server.list_resources()
                if resources:
                    all_resources[name] = resources
            except Exception as e:
                self.logger.error(f"Error getting resources from server '{name}': {e}")
        
        return all_resources
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop() 