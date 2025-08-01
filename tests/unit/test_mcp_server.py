"""Unit tests for MCP server classes."""

import pytest
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mcp.mcp_server import MCPServer
from mcp.generic_mcp_server import GenericMCPServer
from core.models import Message, Context


class TestMCPServer:
    """Test the abstract MCPServer base class."""

    def test_mcp_server_initialization(self):
        """Test MCPServer initialization."""
        config = {
            "name": "test_server",
            "type": "file_system",
            "transport": "stdio",
            "command": "test_command",
            "args": ["arg1", "arg2"]
        }

        # Create a concrete implementation for testing
        class TestServer(MCPServer):
            async def connect(self) -> bool:
                return True

            async def disconnect(self) -> bool:
                return True

            async def send_request(self, method: str, params: dict) -> dict:
                return {"result": "test_response"}

            async def get_capabilities(self) -> dict:
                return {"tools": {}, "resources": {}}

            async def validate_connection(self) -> bool:
                return True

        server = TestServer(config)

        assert server.name == "test_server"
        assert server.server_type == "file_system"
        assert server.transport_type == "stdio"
        assert server.is_connected is False
        assert server.last_used is None
        assert server.request_count == 0
        assert server.error_count == 0
        assert server.capabilities == {}
        assert server.transport is None

    def test_update_usage_stats(self):
        """Test usage statistics update."""
        config = {"name": "test_server"}
        
        class TestServer(MCPServer):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_request(self, method: str, params: dict) -> dict: return {}
            async def get_capabilities(self) -> dict: return {}
            async def validate_connection(self) -> bool: return True

        server = TestServer(config)
        
        # Test successful request
        server.update_usage_stats(success=True)
        assert server.request_count == 1
        assert server.error_count == 0
        assert server.last_used is not None

        # Test failed request
        server.update_usage_stats(success=False)
        assert server.request_count == 2
        assert server.error_count == 1

    def test_get_stats(self):
        """Test getting server statistics."""
        config = {"name": "test_server", "type": "file_system", "transport": "stdio"}
        
        class TestServer(MCPServer):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_request(self, method: str, params: dict) -> dict: return {}
            async def get_capabilities(self) -> dict: return {}
            async def validate_connection(self) -> bool: return True

        server = TestServer(config)
        server.is_connected = True
        server.last_used = datetime.utcnow()
        server.request_count = 5
        server.error_count = 1
        server.capabilities = {"tools": {"test_tool": {}}}

        stats = server.get_stats()

        assert stats["name"] == "test_server"
        assert stats["type"] == "file_system"
        assert stats["transport"] == "stdio"
        assert stats["is_connected"] is True
        assert stats["request_count"] == 5
        assert stats["error_count"] == 1
        assert stats["success_rate"] == 0.8
        assert stats["capabilities"] == {"tools": {"test_tool": {}}}

    def test_get_server_config(self):
        """Test getting server configuration."""
        config = {
            "name": "test_server",
            "type": "file_system",
            "transport": "stdio",
            "command": "test_command"
        }
        
        class TestServer(MCPServer):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_request(self, method: str, params: dict) -> dict: return {}
            async def get_capabilities(self) -> dict: return {}
            async def validate_connection(self) -> bool: return True

        server = TestServer(config)

        server_config = server.get_server_config()

        assert server_config["name"] == "test_server"
        assert server_config["type"] == "file_system"
        assert server_config["transport"] == "stdio"
        assert server_config["config"] == config

    def test_string_representation(self):
        """Test string representation."""
        config = {"name": "test_server", "type": "file_system"}
        
        class TestServer(MCPServer):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_request(self, method: str, params: dict) -> dict: return {}
            async def get_capabilities(self) -> dict: return {}
            async def validate_connection(self) -> bool: return True

        server = TestServer(config)
        server.is_connected = True

        assert str(server) == "MCPServer(name=test_server, type=file_system, connected=True)"
        assert repr(server) == "MCPServer(name='test_server', type='file_system', connected=True)"


class TestGenericMCPServer:
    """Test the GenericMCPServer implementation."""

    @pytest.fixture
    def mcp_config(self):
        return {
            "name": "test_server",
            "type": "file_system",
            "transport": "stdio",
            "command": "echo",
            "args": ["test"]
        }

    @pytest.fixture
    def mcp_server(self, mcp_config):
        return GenericMCPServer(mcp_config)

    @pytest.mark.asyncio
    async def test_generic_mcp_server_initialization(self, mcp_server, mcp_config):
        """Test GenericMCPServer initialization."""
        assert mcp_server.name == "test_server"
        assert mcp_server.server_type == "file_system"
        assert mcp_server.transport_type == "stdio"
        assert mcp_server.transport is None
        assert mcp_server.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_success(self, mcp_server):
        """Test successful connection to MCP server."""
        with patch('mcp.mcp_factory.MCPFactory.create_transport_from_config') as mock_create_transport:
            mock_transport = AsyncMock()
            mock_transport.connect.return_value = True
            mock_create_transport.return_value = mock_transport

            with patch.object(mcp_server, 'get_capabilities') as mock_get_capabilities:
                mock_get_capabilities.return_value = {"tools": {}, "resources": {}}

                result = await mcp_server.connect()

                assert result is True
                assert mcp_server.is_connected is True
                assert mcp_server.transport == mock_transport
                mock_transport.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_transport_failure(self, mcp_server):
        """Test connection failure due to transport failure."""
        with patch('mcp.mcp_factory.MCPFactory.create_transport_from_config') as mock_create_transport:
            mock_transport = AsyncMock()
            mock_transport.connect.return_value = False
            mock_create_transport.return_value = mock_transport

            result = await mcp_server.connect()

            assert result is False
            assert mcp_server.is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect_success(self, mcp_server):
        """Test successful disconnection."""
        # First connect
        with patch('mcp.mcp_factory.MCPFactory.create_transport_from_config') as mock_create_transport:
            mock_transport = AsyncMock()
            mock_transport.connect.return_value = True
            mock_create_transport.return_value = mock_transport

            with patch.object(mcp_server, 'get_capabilities') as mock_get_capabilities:
                mock_get_capabilities.return_value = {"tools": {}, "resources": {}}

                await mcp_server.connect()

        # Then disconnect
        result = await mcp_server.disconnect()

        assert result is True
        assert mcp_server.is_connected is False
        assert mcp_server.transport is None

    @pytest.mark.asyncio
    async def test_send_request_success(self, mcp_server):
        """Test successful request sending."""
        # Setup connection
        with patch('mcp.mcp_factory.MCPFactory.create_transport_from_config') as mock_create_transport:
            mock_transport = AsyncMock()
            mock_transport.connect.return_value = True
            mock_transport.send_request.return_value = {"result": "test_response"}
            mock_create_transport.return_value = mock_transport

            with patch.object(mcp_server, 'get_capabilities') as mock_get_capabilities:
                mock_get_capabilities.return_value = {"tools": {}, "resources": {}}

                await mcp_server.connect()

        # Test request sending
        result = await mcp_server.send_request("test_method", {"param": "value"})

        assert result == {"result": "test_response"}
        assert mcp_server.request_count == 1
        assert mcp_server.error_count == 0
        mock_transport.send_request.assert_called_once_with("test_method", {"param": "value"})

    @pytest.mark.asyncio
    async def test_send_request_not_connected(self, mcp_server):
        """Test request sending when not connected."""
        with pytest.raises(ConnectionError, match="MCP server 'test_server' not connected"):
            await mcp_server.send_request("test_method", {"param": "value"})

    @pytest.mark.asyncio
    async def test_send_request_transport_error(self, mcp_server):
        """Test request sending with transport error."""
        # Setup connection
        with patch('mcp.mcp_factory.MCPFactory.create_transport_from_config') as mock_create_transport:
            mock_transport = AsyncMock()
            mock_transport.connect.return_value = True
            mock_transport.send_request.side_effect = Exception("Transport error")
            mock_create_transport.return_value = mock_transport

            with patch.object(mcp_server, 'get_capabilities') as mock_get_capabilities:
                mock_get_capabilities.return_value = {"tools": {}, "resources": {}}

                await mcp_server.connect()

        # Test request sending
        with pytest.raises(Exception, match="Transport error"):
            await mcp_server.send_request("test_method", {"param": "value"})

        assert mcp_server.request_count == 1
        assert mcp_server.error_count == 1

    @pytest.mark.asyncio
    async def test_get_capabilities_success(self, mcp_server):
        """Test successful capabilities retrieval."""
        # Setup connection
        with patch('mcp.mcp_factory.MCPFactory.create_transport_from_config') as mock_create_transport:
            mock_transport = AsyncMock()
            mock_transport.connect.return_value = True
            mock_transport.send_request.return_value = {
                "result": {
                    "capabilities": {
                        "tools": {"test_tool": {"name": "test_tool"}},
                        "resources": {"test_resource": {"name": "test_resource"}}
                    }
                }
            }
            mock_create_transport.return_value = mock_transport

            with patch.object(mcp_server, 'get_capabilities') as mock_get_capabilities:
                mock_get_capabilities.return_value = {"tools": {}, "resources": {}}

                await mcp_server.connect()

        # Test capabilities retrieval
        capabilities = await mcp_server.get_capabilities()

        expected_capabilities = {
            "tools": {"test_tool": {"name": "test_tool"}},
            "resources": {"test_resource": {"name": "test_resource"}}
        }
        assert capabilities == expected_capabilities
        assert mcp_server.capabilities == expected_capabilities

    @pytest.mark.asyncio
    async def test_get_capabilities_fallback(self, mcp_server):
        """Test capabilities retrieval with fallback to basic capabilities."""
        # Setup connection
        with patch('mcp.mcp_factory.MCPFactory.create_transport_from_config') as mock_create_transport:
            mock_transport = AsyncMock()
            mock_transport.connect.return_value = True
            mock_transport.send_request.side_effect = Exception("Capabilities error")
            mock_create_transport.return_value = mock_transport

            with patch.object(mcp_server, 'get_capabilities') as mock_get_capabilities:
                mock_get_capabilities.return_value = {"tools": {}, "resources": {}}

                await mcp_server.connect()

        # Test capabilities retrieval
        capabilities = await mcp_server.get_capabilities()

        expected_capabilities = {
            "tools": {},
            "resources": {},
            "notifications": {}
        }
        assert capabilities == expected_capabilities
        assert mcp_server.capabilities == expected_capabilities

    @pytest.mark.asyncio
    async def test_validate_connection_success(self, mcp_server):
        """Test successful connection validation."""
        # Setup connection
        with patch('mcp.mcp_factory.MCPFactory.create_transport_from_config') as mock_create_transport:
            mock_transport = AsyncMock()
            mock_transport.connect.return_value = True
            mock_transport.send_request.return_value = {"result": []}
            mock_create_transport.return_value = mock_transport

            with patch.object(mcp_server, 'get_capabilities') as mock_get_capabilities:
                mock_get_capabilities.return_value = {"tools": {}, "resources": {}}

                await mcp_server.connect()

        # Test connection validation
        result = await mcp_server.validate_connection()

        assert result is True

    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, mcp_server):
        """Test connection validation failure."""
        # Setup connection
        with patch('mcp.mcp_factory.MCPFactory.create_transport_from_config') as mock_create_transport:
            mock_transport = AsyncMock()
            mock_transport.connect.return_value = True
            mock_transport.send_request.side_effect = Exception("Validation error")
            mock_create_transport.return_value = mock_transport

            with patch.object(mcp_server, 'get_capabilities') as mock_get_capabilities:
                mock_get_capabilities.return_value = {"tools": {}, "resources": {}}

                await mcp_server.connect()

        # Test connection validation
        result = await mcp_server.validate_connection()

        assert result is False

    @pytest.mark.asyncio
    async def test_call_tool_success(self, mcp_server):
        """Test successful tool call."""
        # Setup connection
        with patch('mcp.mcp_factory.MCPFactory.create_transport_from_config') as mock_create_transport:
            mock_transport = AsyncMock()
            mock_transport.connect.return_value = True
            mock_transport.send_request.return_value = {"result": {"output": "tool_result"}}
            mock_create_transport.return_value = mock_transport

            with patch.object(mcp_server, 'get_capabilities') as mock_get_capabilities:
                mock_get_capabilities.return_value = {"tools": {}, "resources": {}}

                await mcp_server.connect()

        # Test tool call
        result = await mcp_server.call_tool("test_tool", {"param": "value"})

        assert result == {"output": "tool_result"}
        assert mcp_server.request_count == 1
        assert mcp_server.error_count == 0

    @pytest.mark.asyncio
    async def test_list_tools_success(self, mcp_server):
        """Test successful tool listing."""
        # Setup connection
        with patch('mcp.mcp_factory.MCPFactory.create_transport_from_config') as mock_create_transport:
            mock_transport = AsyncMock()
            mock_transport.connect.return_value = True
            mock_transport.send_request.return_value = {
                "result": {
                    "tools": [
                        {"name": "tool1", "description": "First tool"},
                        {"name": "tool2", "description": "Second tool"}
                    ]
                }
            }
            mock_create_transport.return_value = mock_transport

            with patch.object(mcp_server, 'get_capabilities') as mock_get_capabilities:
                mock_get_capabilities.return_value = {"tools": {}, "resources": {}}

                await mcp_server.connect()

        # Test tool listing
        tools = await mcp_server.list_tools()

        expected_tools = [
            {"name": "tool1", "description": "First tool"},
            {"name": "tool2", "description": "Second tool"}
        ]
        assert tools == expected_tools

    @pytest.mark.asyncio
    async def test_list_resources_success(self, mcp_server):
        """Test successful resource listing."""
        # Setup connection
        with patch('mcp.mcp_factory.MCPFactory.create_transport_from_config') as mock_create_transport:
            mock_transport = AsyncMock()
            mock_transport.connect.return_value = True
            mock_transport.send_request.return_value = {
                "result": {
                    "resources": [
                        {"name": "resource1", "type": "file"},
                        {"name": "resource2", "type": "directory"}
                    ]
                }
            }
            mock_create_transport.return_value = mock_transport

            with patch.object(mcp_server, 'get_capabilities') as mock_get_capabilities:
                mock_get_capabilities.return_value = {"tools": {}, "resources": {}}

                await mcp_server.connect()

        # Test resource listing
        resources = await mcp_server.list_resources()

        expected_resources = [
            {"name": "resource1", "type": "file"},
            {"name": "resource2", "type": "directory"}
        ]
        assert resources == expected_resources

    def test_has_capability(self, mcp_server):
        """Test capability checking."""
        mcp_server.capabilities = {
            "tools": {"test_tool": {}},
            "resources": {"test_resource": {}}
        }

        assert mcp_server.has_capability("tools") is True
        assert mcp_server.has_capability("resources") is True
        assert mcp_server.has_capability("nonexistent") is False

    def test_get_capability_info(self, mcp_server):
        """Test capability info retrieval."""
        mcp_server.capabilities = {
            "tools": {"test_tool": {"name": "test_tool"}},
            "resources": {"test_resource": {"name": "test_resource"}}
        }

        tools_info = mcp_server.get_capability_info("tools")
        assert tools_info == {"test_tool": {"name": "test_tool"}}

        resources_info = mcp_server.get_capability_info("resources")
        assert resources_info == {"test_resource": {"name": "test_resource"}}

        # Test nonexistent capability
        nonexistent_info = mcp_server.get_capability_info("nonexistent")
        assert nonexistent_info is None

    def test_get_transport_info(self, mcp_server):
        """Test transport info retrieval."""
        # Test with no transport
        transport_info = mcp_server.get_transport_info()
        assert transport_info == {}

        # Test with transport
        mock_transport = AsyncMock()
        mock_transport.is_connected = True
        mock_transport.config = {"command": "test_command"}
        mcp_server.transport = mock_transport

        transport_info = mcp_server.get_transport_info()
        assert transport_info["type"] == "stdio"
        assert transport_info["connected"] is True
        assert transport_info["config"] == {"command": "test_command"} 