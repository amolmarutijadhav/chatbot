"""Factory for creating MCP servers and transports."""

from typing import Dict, Any, Type
from .mcp_server import MCPServer
from .transports.base_transport import BaseTransport
from .transports.stdio_transport import STDIOTransport
from .transports.http_transport import HTTPTransport
from utils.logger import get_logger


class MCPFactory:
    """Factory for creating MCP servers and transports."""
    
    # Registry of available transports
    _transports: Dict[str, Type[BaseTransport]] = {
        "stdio": STDIOTransport,
        "http": HTTPTransport,
    }
    
    @classmethod
    def register_transport(cls, name: str, transport_class: Type[BaseTransport]):
        """Register a new transport type."""
        cls._transports[name] = transport_class
        logger = get_logger(__name__)
        logger.info(f"Registered MCP transport: {name}")
    
    @classmethod
    def get_available_transports(cls) -> list[str]:
        """Get list of available transport names."""
        return list(cls._transports.keys())
    
    @classmethod
    def create_transport(cls, transport_type: str, config: Dict[str, Any]) -> BaseTransport:
        """Create a transport instance."""
        if transport_type not in cls._transports:
            available = ", ".join(cls.get_available_transports())
            raise ValueError(f"Unknown transport type '{transport_type}'. Available: {available}")
        
        transport_class = cls._transports[transport_type]
        
        try:
            transport = transport_class(config)
            logger = get_logger(__name__)
            logger.info(f"Created MCP transport: {transport_type}")
            return transport
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Failed to create transport '{transport_type}': {e}")
            raise
    
    @classmethod
    def create_transport_from_config(cls, config: Dict[str, Any]) -> BaseTransport:
        """Create a transport from configuration."""
        # If config has a 'transport' key, it's a server config, extract transport config
        if "transport" in config and isinstance(config["transport"], dict):
            transport_config = config["transport"]
            transport_type = transport_config.get("type", "stdio")
            return cls.create_transport(transport_type, transport_config)
        else:
            # Direct transport config
            transport_type = config.get("type", "stdio")
            return cls.create_transport(transport_type, config)
    
    @classmethod
    def validate_transport_config(cls, transport_type: str, config: Dict[str, Any]) -> bool:
        """Validate transport configuration."""
        try:
            transport = cls.create_transport(transport_type, config)
            
            # Check required fields based on transport type
            if transport_type == "stdio":
                if not config.get("command"):
                    logger = get_logger(__name__)
                    logger.error("Missing required field 'command' for STDIO transport")
                    return False
            elif transport_type == "http":
                if not config.get("base_url"):
                    logger = get_logger(__name__)
                    logger.error("Missing required field 'base_url' for HTTP transport")
                    return False
            
            return True
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Invalid configuration for transport '{transport_type}': {e}")
            return False
    
    @classmethod
    def create_mcp_server(cls, config: Dict[str, Any]) -> MCPServer:
        """Create an MCP server instance."""
        # This would be implemented when we have concrete MCP server implementations
        # For now, we'll create a generic server that uses the transport
        from .generic_mcp_server import GenericMCPServer
        return GenericMCPServer(config)
    
    @classmethod
    def validate_server_config(cls, config: Dict[str, Any]) -> bool:
        """Validate server configuration."""
        try:
            # Check required fields
            required_fields = ["name", "type", "transport"]
            for field in required_fields:
                if not config.get(field):
                    logger = get_logger(__name__)
                    logger.error(f"Missing required field '{field}' for MCP server")
                    return False
            
            # Validate transport configuration
            transport_config = config.get("transport", {})
            transport_type = transport_config.get("type", "stdio")
            if not cls.validate_transport_config(transport_type, transport_config):
                return False
            
            return True
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Invalid server configuration: {e}")
            return False 