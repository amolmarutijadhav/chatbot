"""Abstract base class for MCP transports."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json


class BaseTransport(ABC):
    """Abstract base class for MCP transports."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the transport with configuration."""
        self.config = config
        self.is_connected = False
        
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the transport."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the transport."""
        pass
    
    @abstractmethod
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message through the transport."""
        pass
    
    @abstractmethod
    async def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive a message from the transport."""
        pass
    
    def format_message(self, method: str, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Format a message for the transport."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
    
    def parse_message(self, message: str) -> Dict[str, Any]:
        """Parse a message from the transport."""
        try:
            return json.loads(message)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON message: {e}")
    
    def validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate a response from the transport."""
        if "jsonrpc" not in response or response["jsonrpc"] != "2.0":
            return False
        
        if "id" not in response:
            return False
        
        # Check for error
        if "error" in response:
            return False
        
        # Check for result
        if "result" not in response:
            return False
        
        return True
    
    def get_error_from_response(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract error message from response."""
        if "error" in response:
            error = response["error"]
            return f"Error {error.get('code', 'unknown')}: {error.get('message', 'Unknown error')}"
        return None
    
    def get_result_from_response(self, response: Dict[str, Any]) -> Any:
        """Extract result from response."""
        if "result" in response:
            return response["result"]
        return None 