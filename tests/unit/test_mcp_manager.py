"""Unit tests for MCP manager."""

import pytest
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mcp.mcp_manager import MCPManager
from mcp.generic_mcp_server import GenericMCPServer


class TestMCPManager:
    """Test the MCP manager."""

    @pytest.fixture
    def mcp_config(self):
        return {
            "health_check_interval": 300,
            "auto_discovery": False,
            "servers": {
                "file_server": {
                    "name": "file_server",
                    "type": "file_system",
                    "transport": "stdio",
                    "command": "echo",
                    "args": ["test"]
                },
                "db_server": {
                    "name": "db_server",
                    "type": "database",
                    "transport": "http",
                    "base_url": "http://localhost:8080"
                }
            }
        }

    @pytest.fixture
    def mcp_manager(self, mcp_config):
        return MCPManager(mcp_config)

    @pytest.mark.asyncio
    async def test_mcp_manager_initialization(self, mcp_manager, mcp_config):
        """Test MCP manager initialization."""
        assert mcp_manager.config == mcp_config
        assert mcp_manager.health_check_interval == 300
        assert mcp_manager.auto_discovery is False
        assert mcp_manager.servers == {}
        assert mcp_manager.health_check_task is None

    @pytest.mark.asyncio
    async def test_start_success(self, mcp_manager):
        """Test successful start of MCP manager."""
        with patch.object(mcp_manager, 'add_server') as mock_add_server:
            mock_add_server.return_value = True

            await mcp_manager.start()

            assert mock_add_server.call_count == 2
            assert mcp_manager.health_check_task is not None

            # Cleanup
            if mcp_manager.health_check_task:
                mcp_manager.health_check_task.cancel()
                try:
                    await mcp_manager.health_check_task
                except asyncio.CancelledError:
                    pass

    @pytest.mark.asyncio
    async def test_start_with_server_failure(self, mcp_manager):
        """Test start with server connection failure."""
        with patch.object(mcp_manager, 'add_server') as mock_add_server:
            mock_add_server.return_value = False

            await mcp_manager.start()

            assert mock_add_server.call_count == 2
            assert len(mcp_manager.servers) == 0

    @pytest.mark.asyncio
    async def test_stop_success(self, mcp_manager):
        """Test successful stop of MCP manager."""
        # First start
        with patch.object(mcp_manager, 'add_server') as mock_add_server:
            mock_add_server.return_value = True
            await mcp_manager.start()

        # Then stop
        with patch.object(mcp_manager, 'remove_server') as mock_remove_server:
            mock_remove_server.return_value = True

            await mcp_manager.stop()

            assert mock_remove_server.call_count == 2
            assert mcp_manager.health_check_task is None

    @pytest.mark.asyncio
    async def test_add_server_success(self, mcp_manager):
        """Test successful server addition."""
        with patch('mcp.mcp_factory.MCPFactory.validate_server_config') as mock_validate:
            with patch('mcp.mcp_factory.MCPFactory.create_mcp_server') as mock_create:
                mock_validate.return_value = True
                mock_server = AsyncMock()
                mock_server.connect.return_value = True
                mock_create.return_value = mock_server

                result = await mcp_manager.add_server("test_server", {"name": "test"})

                assert result is True
                assert "test_server" in mcp_manager.servers
                assert mcp_manager.servers["test_server"] == mock_server

    @pytest.mark.asyncio
    async def test_add_server_validation_failure(self, mcp_manager):
        """Test server addition with validation failure."""
        with patch('mcp.mcp_factory.MCPFactory.validate_server_config') as mock_validate:
            mock_validate.return_value = False

            result = await mcp_manager.add_server("test_server", {"name": "test"})

            assert result is False
            assert "test_server" not in mcp_manager.servers

    @pytest.mark.asyncio
    async def test_add_server_connection_failure(self, mcp_manager):
        """Test server addition with connection failure."""
        with patch('mcp.mcp_factory.MCPFactory.validate_server_config') as mock_validate:
            with patch('mcp.mcp_factory.MCPFactory.create_mcp_server') as mock_create:
                mock_validate.return_value = True
                mock_server = AsyncMock()
                mock_server.connect.return_value = False
                mock_create.return_value = mock_server

                result = await mcp_manager.add_server("test_server", {"name": "test"})

                assert result is False
                assert "test_server" not in mcp_manager.servers

    @pytest.mark.asyncio
    async def test_remove_server_success(self, mcp_manager):
        """Test successful server removal."""
        # First add a server
        mock_server = AsyncMock()
        mcp_manager.servers["test_server"] = mock_server

        result = await mcp_manager.remove_server("test_server")

        assert result is True
        assert "test_server" not in mcp_manager.servers
        mock_server.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_nonexistent_server(self, mcp_manager):
        """Test removal of nonexistent server."""
        result = await mcp_manager.remove_server("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_call_tool_success(self, mcp_manager):
        """Test successful tool call."""
        # Setup servers
        mock_server1 = AsyncMock()
        mock_server1.is_connected = True
        mock_server1.call_tool.return_value = {"result": "from server 1"}

        mock_server2 = AsyncMock()
        mock_server2.is_connected = True
        mock_server2.call_tool.return_value = {"result": "from server 2"}

        mcp_manager.servers["file_server"] = mock_server1
        mcp_manager.servers["db_server"] = mock_server2

        result = await mcp_manager.call_tool("test_tool", {"param": "value"})

        assert result == {"result": "from server 1"}
        mock_server1.call_tool.assert_called_once_with("test_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_with_specific_server(self, mcp_manager):
        """Test tool call with specific server."""
        mock_server = AsyncMock()
        mock_server.is_connected = True
        mock_server.call_tool.return_value = {"result": "specific result"}

        mcp_manager.servers["db_server"] = mock_server

        result = await mcp_manager.call_tool("test_tool", {"param": "value"}, server_name="db_server")

        assert result == {"result": "specific result"}
        mock_server.call_tool.assert_called_once_with("test_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_server_not_found(self, mcp_manager):
        """Test tool call with server not found."""
        with pytest.raises(ValueError, match="Server 'nonexistent' not found"):
            await mcp_manager.call_tool("test_tool", {"param": "value"}, server_name="nonexistent")

    @pytest.mark.asyncio
    async def test_call_tool_no_servers(self, mcp_manager):
        """Test tool call with no servers available."""
        with pytest.raises(RuntimeError, match="No MCP servers available"):
            await mcp_manager.call_tool("test_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_no_servers_with_tool(self, mcp_manager):
        """Test tool call when no servers have the requested tool."""
        # Setup servers without the tool
        mock_server = AsyncMock()
        mock_server.is_connected = True
        mock_server.has_capability.return_value = False
        mcp_manager.servers["file_server"] = mock_server

        with pytest.raises(ValueError, match="No servers found with tool 'test_tool'"):
            await mcp_manager.call_tool("test_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_with_fallback(self, mcp_manager):
        """Test tool call with fallback to second server."""
        # Setup servers
        mock_server1 = AsyncMock()
        mock_server1.is_connected = True
        mock_server1.call_tool.side_effect = Exception("Server 1 failed")

        mock_server2 = AsyncMock()
        mock_server2.is_connected = True
        mock_server2.call_tool.return_value = {"result": "from server 2"}

        mcp_manager.servers["file_server"] = mock_server1
        mcp_manager.servers["db_server"] = mock_server2

        result = await mcp_manager.call_tool("test_tool", {"param": "value"})

        assert result == {"result": "from server 2"}
        mock_server1.call_tool.assert_called_once()
        mock_server2.call_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_all_servers_fail(self, mcp_manager):
        """Test tool call when all servers fail."""
        # Setup servers
        mock_server1 = AsyncMock()
        mock_server1.is_connected = True
        mock_server1.call_tool.side_effect = Exception("Server 1 failed")

        mock_server2 = AsyncMock()
        mock_server2.is_connected = True
        mock_server2.call_tool.side_effect = Exception("Server 2 failed")

        mcp_manager.servers["file_server"] = mock_server1
        mcp_manager.servers["db_server"] = mock_server2

        with pytest.raises(RuntimeError, match="All MCP servers failed for tool 'test_tool'"):
            await mcp_manager.call_tool("test_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_find_servers_with_tool(self, mcp_manager):
        """Test finding servers with a specific tool."""
        # Setup servers
        mock_server1 = AsyncMock()
        mock_server1.has_capability.return_value = True
        mock_server1.get_capability_info.return_value = ["test_tool", "other_tool"]

        mock_server2 = AsyncMock()
        mock_server2.has_capability.return_value = True
        mock_server2.get_capability_info.return_value = ["different_tool"]

        mock_server3 = AsyncMock()
        mock_server3.has_capability.return_value = False

        mcp_manager.servers["file_server"] = mock_server1
        mcp_manager.servers["db_server"] = mock_server2
        mcp_manager.servers["web_server"] = mock_server3

        servers_with_tool = await mcp_manager._find_servers_with_tool("test_tool")

        assert servers_with_tool == ["file_server"]

    @pytest.mark.asyncio
    async def test_get_server_stats(self, mcp_manager):
        """Test getting server statistics."""
        # Setup servers
        mock_server1 = AsyncMock()
        mock_server1.is_connected = True
        mock_server1.get_stats.return_value = {
            "name": "file_server",
            "request_count": 10,
            "error_count": 1
        }

        mock_server2 = AsyncMock()
        mock_server2.is_connected = False
        mock_server2.get_stats.return_value = {
            "name": "db_server",
            "request_count": 5,
            "error_count": 0
        }

        mcp_manager.servers["file_server"] = mock_server1
        mcp_manager.servers["db_server"] = mock_server2

        stats = await mcp_manager.get_server_stats()

        assert stats["total_servers"] == 2
        assert stats["connected_servers"] == 1
        assert "file_server" in stats["servers"]
        assert "db_server" in stats["servers"]

    @pytest.mark.asyncio
    async def test_health_check_success(self, mcp_manager):
        """Test successful health check."""
        # Setup servers
        mock_server1 = AsyncMock()
        mock_server1.is_connected = True
        mock_server1.validate_connection.return_value = True

        mock_server2 = AsyncMock()
        mock_server2.is_connected = True
        mock_server2.validate_connection.return_value = False

        mcp_manager.servers["file_server"] = mock_server1
        mcp_manager.servers["db_server"] = mock_server2

        health_status = await mcp_manager.health_check()

        assert health_status["file_server"] is True
        assert health_status["db_server"] is False

    @pytest.mark.asyncio
    async def test_health_check_with_reconnection(self, mcp_manager):
        """Test health check with server reconnection."""
        # Setup server
        mock_server = AsyncMock()
        mock_server.is_connected = True
        mock_server.validate_connection.return_value = False

        mcp_manager.servers["file_server"] = mock_server

        await mcp_manager.health_check()

        # Should attempt to disconnect and reconnect
        mock_server.disconnect.assert_called_once()
        mock_server.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_loop(self, mcp_manager):
        """Test health check loop."""
        with patch.object(mcp_manager, 'health_check') as mock_health_check:
            mock_health_check.return_value = {}

            # Start health check task
            mcp_manager.health_check_interval = 0.1
            task = asyncio.create_task(mcp_manager._health_check_loop())

            # Wait a bit for the loop to run
            await asyncio.sleep(0.2)

            # Cancel the task
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            # Should have called health_check at least once
            assert mock_health_check.call_count >= 1

    def test_get_server(self, mcp_manager):
        """Test getting a specific server."""
        mock_server = AsyncMock()
        mcp_manager.servers["test_server"] = mock_server

        server = mcp_manager.get_server("test_server")
        assert server == mock_server

        # Test nonexistent server
        server = mcp_manager.get_server("nonexistent")
        assert server is None

    def test_list_servers(self, mcp_manager):
        """Test listing all servers."""
        mcp_manager.servers["server1"] = AsyncMock()
        mcp_manager.servers["server2"] = AsyncMock()

        servers = mcp_manager.list_servers()
        assert set(servers) == {"server1", "server2"}

    def test_is_server_available(self, mcp_manager):
        """Test checking if server is available."""
        mock_server = AsyncMock()
        mock_server.is_connected = True
        mcp_manager.servers["test_server"] = mock_server

        assert mcp_manager.is_server_available("test_server") is True

        # Test disconnected server
        mock_server.is_connected = False
        assert mcp_manager.is_server_available("test_server") is False

        # Test nonexistent server
        assert mcp_manager.is_server_available("nonexistent") is False

    @pytest.mark.asyncio
    async def test_discover_servers(self, mcp_manager):
        """Test server discovery."""
        discovered_servers = await mcp_manager.discover_servers()

        assert discovered_servers == []

    @pytest.mark.asyncio
    async def test_get_all_tools(self, mcp_manager):
        """Test getting all tools from all servers."""
        # Setup servers
        mock_server1 = AsyncMock()
        mock_server1.list_tools.return_value = [
            {"name": "tool1", "description": "First tool"},
            {"name": "tool2", "description": "Second tool"}
        ]

        mock_server2 = AsyncMock()
        mock_server2.list_tools.side_effect = Exception("Server error")

        mcp_manager.servers["file_server"] = mock_server1
        mcp_manager.servers["db_server"] = mock_server2

        all_tools = await mcp_manager.get_all_tools()

        assert "file_server" in all_tools
        assert len(all_tools["file_server"]) == 2
        assert "db_server" not in all_tools  # Should be excluded due to error

    @pytest.mark.asyncio
    async def test_get_all_resources(self, mcp_manager):
        """Test getting all resources from all servers."""
        # Setup servers
        mock_server1 = AsyncMock()
        mock_server1.list_resources.return_value = [
            {"name": "resource1", "type": "file"},
            {"name": "resource2", "type": "directory"}
        ]

        mock_server2 = AsyncMock()
        mock_server2.list_resources.side_effect = Exception("Server error")

        mcp_manager.servers["file_server"] = mock_server1
        mcp_manager.servers["db_server"] = mock_server2

        all_resources = await mcp_manager.get_all_resources()

        assert "file_server" in all_resources
        assert len(all_resources["file_server"]) == 2
        assert "db_server" not in all_resources  # Should be excluded due to error

    @pytest.mark.asyncio
    async def test_context_manager(self, mcp_manager):
        """Test async context manager."""
        with patch.object(mcp_manager, 'start') as mock_start:
            with patch.object(mcp_manager, 'stop') as mock_stop:
                async with mcp_manager as manager:
                    assert manager == mcp_manager

                mock_start.assert_called_once()
                mock_stop.assert_called_once() 