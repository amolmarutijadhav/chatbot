"""Unit tests for MCP factory."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mcp.mcp_factory import MCPFactory
from mcp.transports.base_transport import BaseTransport
from mcp.transports.stdio_transport import STDIOTransport
from mcp.transports.http_transport import HTTPTransport


class TestMCPFactory:
    """Test the MCP factory."""

    def test_get_available_transports(self):
        """Test getting available transports."""
        transports = MCPFactory.get_available_transports()
        
        assert "stdio" in transports
        assert "http" in transports
        assert isinstance(transports, list)

    def test_register_transport(self):
        """Test registering a new transport."""
        # Create a test transport class
        class TestTransport(BaseTransport):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_message(self, message: dict) -> dict: return {}
            async def receive_message(self) -> dict: return {}

        # Register the transport
        MCPFactory.register_transport("test_transport", TestTransport)

        # Check if it's available
        transports = MCPFactory.get_available_transports()
        assert "test_transport" in transports

        # Clean up - remove the test transport
        del MCPFactory._transports["test_transport"]

    def test_create_transport_success(self):
        """Test successful transport creation."""
        config = {
            "command": "echo",
            "args": ["test"]
        }

        transport = MCPFactory.create_transport("stdio", config)

        assert isinstance(transport, STDIOTransport)
        assert transport.command == "echo"
        assert transport.args == ["test"]

    def test_create_transport_unknown_type(self):
        """Test creating transport with unknown type."""
        config = {"command": "test"}

        with pytest.raises(ValueError, match="Unknown transport type 'unknown'"):
            MCPFactory.create_transport("unknown", config)

    def test_create_transport_from_config(self):
        """Test creating transport from configuration."""
        config = {
            "transport": "stdio",
            "command": "echo",
            "args": ["test"]
        }

        transport = MCPFactory.create_transport_from_config(config)

        assert isinstance(transport, STDIOTransport)
        assert transport.command == "echo"

    def test_create_transport_from_config_default(self):
        """Test creating transport from config with default transport."""
        config = {
            "command": "echo",
            "args": ["test"]
        }

        transport = MCPFactory.create_transport_from_config(config)

        assert isinstance(transport, STDIOTransport)
        assert transport.command == "echo"

    def test_create_transport_exception_handling(self):
        """Test exception handling during transport creation."""
        config = {
            "command": "echo",
            "args": ["test"]
        }

        # Mock the transport class to raise an exception
        with patch('mcp.mcp_factory.STDIOTransport') as mock_transport_class:
            mock_transport_class.side_effect = Exception("Transport creation failed")

            with pytest.raises(Exception, match="Transport creation failed"):
                MCPFactory.create_transport("stdio", config)

    def test_validate_transport_config_success(self):
        """Test successful transport configuration validation."""
        config = {
            "command": "echo",
            "args": ["test"]
        }

        result = MCPFactory.validate_transport_config("stdio", config)

        assert result is True

    def test_validate_transport_config_missing_required_fields(self):
        """Test transport configuration validation with missing fields."""
        config = {
            "args": ["test"]
            # Missing command for stdio
        }

        result = MCPFactory.validate_transport_config("stdio", config)

        assert result is False

    def test_validate_transport_config_http_missing_base_url(self):
        """Test HTTP transport configuration validation with missing base_url."""
        config = {
            "api_key": "test_key"
            # Missing base_url for http
        }

        result = MCPFactory.validate_transport_config("http", config)

        assert result is False

    def test_validate_transport_config_creation_failure(self):
        """Test transport configuration validation with creation failure."""
        config = {
            "command": "echo",
            "args": ["test"]
        }

        # Mock the create_transport method to raise an exception
        with patch.object(MCPFactory, 'create_transport') as mock_create:
            mock_create.side_effect = Exception("Creation failed")

            result = MCPFactory.validate_transport_config("stdio", config)

            assert result is False

    def test_validate_transport_config_unknown_type(self):
        """Test transport configuration validation with unknown type."""
        config = {
            "command": "test"
        }

        result = MCPFactory.validate_transport_config("unknown", config)

        assert result is False

    def test_create_mcp_server(self):
        """Test creating MCP server."""
        config = {
            "name": "test_server",
            "type": "file_system",
            "transport": "stdio",
            "command": "echo",
            "args": ["test"]
        }

        server = MCPFactory.create_mcp_server(config)

        assert server is not None
        assert server.name == "test_server"
        assert server.server_type == "file_system"
        assert server.transport_type == "stdio"

    def test_validate_server_config_success(self):
        """Test successful server configuration validation."""
        config = {
            "name": "test_server",
            "type": "file_system",
            "transport": "stdio",
            "command": "echo",
            "args": ["test"]
        }

        result = MCPFactory.validate_server_config(config)

        assert result is True

    def test_validate_server_config_missing_required_fields(self):
        """Test server configuration validation with missing fields."""
        config = {
            "name": "test_server",
            "type": "file_system"
            # Missing transport
        }

        result = MCPFactory.validate_server_config(config)

        assert result is False

    def test_validate_server_config_missing_name(self):
        """Test server configuration validation with missing name."""
        config = {
            "type": "file_system",
            "transport": "stdio",
            "command": "echo"
        }

        result = MCPFactory.validate_server_config(config)

        assert result is False

    def test_validate_server_config_missing_type(self):
        """Test server configuration validation with missing type."""
        config = {
            "name": "test_server",
            "transport": "stdio",
            "command": "echo"
        }

        result = MCPFactory.validate_server_config(config)

        assert result is False

    def test_validate_server_config_invalid_transport(self):
        """Test server configuration validation with invalid transport."""
        config = {
            "name": "test_server",
            "type": "file_system",
            "transport": "stdio",
            "command": "echo"
        }

        # Mock transport validation to fail
        with patch.object(MCPFactory, 'validate_transport_config') as mock_validate:
            mock_validate.return_value = False

            result = MCPFactory.validate_server_config(config)

            assert result is False

    def test_validate_server_config_exception_handling(self):
        """Test server configuration validation with exception."""
        config = {
            "name": "test_server",
            "type": "file_system",
            "transport": "stdio",
            "command": "echo"
        }

        # Mock transport validation to raise exception
        with patch.object(MCPFactory, 'validate_transport_config') as mock_validate:
            mock_validate.side_effect = Exception("Validation error")

            result = MCPFactory.validate_server_config(config)

            assert result is False

    def test_factory_singleton_behavior(self):
        """Test that factory maintains singleton-like behavior for transports."""
        config1 = {
            "command": "echo",
            "args": ["test1"]
        }

        config2 = {
            "command": "echo",
            "args": ["test2"]
        }

        transport1 = MCPFactory.create_transport("stdio", config1)
        transport2 = MCPFactory.create_transport("stdio", config2)

        # Each call should create a new instance
        assert transport1 is not transport2
        assert transport1.args == ["test1"]
        assert transport2.args == ["test2"]

    def test_factory_transport_registry_integrity(self):
        """Test that transport registry maintains integrity."""
        original_transports = MCPFactory._transports.copy()

        # Test that we can't accidentally modify the registry
        try:
            MCPFactory._transports["test"] = None
            assert "test" in MCPFactory._transports
        finally:
            # Clean up
            if "test" in MCPFactory._transports:
                del MCPFactory._transports["test"]

        # Verify original transports are still there
        for transport_name in original_transports:
            assert transport_name in MCPFactory._transports
            assert MCPFactory._transports[transport_name] == original_transports[transport_name]

    def test_factory_error_messages(self):
        """Test that factory provides clear error messages."""
        # Test unknown transport error
        try:
            MCPFactory.create_transport("nonexistent", {})
        except ValueError as e:
            error_msg = str(e)
            assert "Unknown transport type 'nonexistent'" in error_msg
            assert "Available:" in error_msg
            assert "stdio" in error_msg  # Should list available transports
            assert "http" in error_msg

    def test_factory_config_validation_comprehensive(self):
        """Test comprehensive configuration validation."""
        # Test stdio transport with all required fields
        valid_stdio_config = {
            "command": "echo",
            "args": ["test"]
        }
        assert MCPFactory.validate_transport_config("stdio", valid_stdio_config) is True

        # Test stdio transport with missing command
        invalid_stdio_config = {
            "args": ["test"]
        }
        assert MCPFactory.validate_transport_config("stdio", invalid_stdio_config) is False

        # Test http transport with all required fields
        valid_http_config = {
            "base_url": "http://localhost:8080",
            "api_key": "test_key"
        }
        assert MCPFactory.validate_transport_config("http", valid_http_config) is True

        # Test http transport with missing base_url
        invalid_http_config = {
            "api_key": "test_key"
        }
        assert MCPFactory.validate_transport_config("http", invalid_http_config) is False

        # Test with empty config
        assert MCPFactory.validate_transport_config("stdio", {}) is False

    def test_factory_server_config_validation_comprehensive(self):
        """Test comprehensive server configuration validation."""
        # Test with all required fields
        valid_config = {
            "name": "test_server",
            "type": "file_system",
            "transport": "stdio",
            "command": "echo"
        }
        assert MCPFactory.validate_server_config(valid_config) is True

        # Test with missing name
        invalid_config1 = {
            "type": "file_system",
            "transport": "stdio",
            "command": "echo"
        }
        assert MCPFactory.validate_server_config(invalid_config1) is False

        # Test with missing type
        invalid_config2 = {
            "name": "test_server",
            "transport": "stdio",
            "command": "echo"
        }
        assert MCPFactory.validate_server_config(invalid_config2) is False

        # Test with missing transport
        invalid_config3 = {
            "name": "test_server",
            "type": "file_system",
            "command": "echo"
        }
        assert MCPFactory.validate_server_config(invalid_config3) is False

        # Test with empty config
        assert MCPFactory.validate_server_config({}) is False 