"""HTTP transport implementation for MCP servers."""

import aiohttp
import json
import uuid
from typing import Dict, Any, Optional
from urllib.parse import urljoin

from .base_transport import BaseTransport
from utils.logger import LoggerMixin


class HTTPTransport(BaseTransport, LoggerMixin):
    """HTTP transport for MCP servers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize HTTP transport."""
        super().__init__(config)
        self.base_url = config.get("base_url", "")
        self.api_key = config.get("api_key", "")
        self.timeout = config.get("timeout", 30)
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_id = 0
        
    async def connect(self) -> bool:
        """Connect to the MCP server via HTTP."""
        try:
            if not self.base_url:
                self.logger.error("No base URL specified for HTTP transport")
                return False
            
            # Create aiohttp session
            headers = {
                "Content-Type": "application/json"
            }
            
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
            
            # Test connection
            if await self.validate_connection():
                self.is_connected = True
                self.logger.info(f"Connected to MCP server via HTTP: {self.base_url}")
                return True
            else:
                self.logger.error("Failed to validate HTTP connection")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server via HTTP: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from the MCP server."""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            self.is_connected = False
            self.logger.info("Disconnected from MCP server via HTTP")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from MCP server: {e}")
            return False
    
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to the MCP server via HTTP."""
        if not self.is_connected or not self.session:
            raise ConnectionError("HTTP transport not connected")
        
        try:
            # Send POST request
            url = urljoin(self.base_url, "/mcp")
            async with self.session.post(url, json=message) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Validate response
                    if not self.validate_response(data):
                        error_msg = self.get_error_from_response(data)
                        if error_msg:
                            raise Exception(error_msg)
                        else:
                            raise Exception("Invalid response from MCP server")
                    
                    return data
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP error {response.status}: {error_text}")
                    
        except Exception as e:
            self.logger.error(f"Error sending message via HTTP: {e}")
            raise
    
    async def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive a message from the MCP server via HTTP."""
        # HTTP transport doesn't support receiving messages directly
        # Messages are sent via POST requests and responses are returned
        return None
    
    async def validate_connection(self) -> bool:
        """Validate the HTTP connection."""
        try:
            if not self.session:
                return False
            
            # Try to get server info
            url = urljoin(self.base_url, "/health")
            async with self.session.get(url) as response:
                return response.status == 200
                
        except Exception:
            return False
    
    def get_next_request_id(self) -> str:
        """Get the next request ID."""
        self.request_id += 1
        return str(self.request_id)
    
    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the MCP server."""
        request_id = self.get_next_request_id()
        message = self.format_message(method, params, request_id)
        return await self.send_message(message)
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        try:
            if not self.session:
                return {}
            
            url = urljoin(self.base_url, "/info")
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {}
                    
        except Exception as e:
            self.logger.error(f"Error getting server info: {e}")
            return {} 