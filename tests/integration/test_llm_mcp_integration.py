"""Integration tests for LLM and MCP integration."""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from llm.llm_manager import LLMManager
from llm.llm_factory import LLMFactory
from llm.providers.openai_provider import OpenAIProvider
from mcp.mcp_manager import MCPManager
from mcp.mcp_factory import MCPFactory
from mcp.generic_mcp_server import GenericMCPServer
from mcp.transports.stdio_transport import STDIOTransport
from mcp.transports.http_transport import HTTPTransport
from core.models import Message, Context
from utils.config_manager import ConfigurationManager
from utils.logger import setup_logging


class TestLLMIntegration:
    """Integration tests for LLM components."""

    @pytest.fixture
    def llm_config(self):
        return {
            "default_provider": "openai",
            "fallback_providers": ["anthropic"],
            "load_balancing": "round_robin",
            "health_check_interval": 300,
            "providers": {
                "openai": {
                    "name": "openai",
                    "model": "gpt-3.5-turbo",
                    "base_url": "https://api.openai.com/v1",
                    "api_key": "test_key",
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            }
        }

    @pytest.fixture
    def llm_manager(self, llm_config):
        return LLMManager(llm_config)

    @pytest.mark.asyncio
    async def test_llm_manager_lifecycle(self, llm_manager):
        """Test complete LLM manager lifecycle."""
        # Test start
        with patch.object(llm_manager, 'add_provider') as mock_add_provider:
            mock_add_provider.return_value = True

            await llm_manager.start()

            assert mock_add_provider.call_count == 1
            assert llm_manager.health_check_task is not None

            # Cleanup
            if llm_manager.health_check_task:
                llm_manager.health_check_task.cancel()
                try:
                    await llm_manager.health_check_task
                except asyncio.CancelledError:
                    pass

        # Test stop
        with patch.object(llm_manager, 'remove_provider') as mock_remove_provider:
            mock_remove_provider.return_value = True

            await llm_manager.stop()

            assert mock_remove_provider.call_count == 1
            assert llm_manager.health_check_task is None

    @pytest.mark.asyncio
    async def test_llm_factory_integration(self):
        """Test LLM factory integration."""
        # Test provider registration
        class TestProvider(OpenAIProvider):
            pass

        LLMFactory.register_provider("test_provider", TestProvider)

        # Verify registration
        providers = LLMFactory.get_available_providers()
        assert "test_provider" in providers

        # Test provider creation
        config = {
            "name": "test_provider",
            "model": "test_model",
            "api_key": "test_key"
        }

        provider = LLMFactory.create_provider("test_provider", config)
        assert isinstance(provider, TestProvider)

        # Cleanup
        del LLMFactory._providers["test_provider"]

    @pytest.mark.asyncio
    async def test_llm_provider_integration(self):
        """Test LLM provider integration."""
        config = {
            "name": "openai",
            "model": "gpt-3.5-turbo",
            "base_url": "https://api.openai.com/v1",
            "api_key": "test_key"
        }

        provider = OpenAIProvider(config)

        # Test connection (will fail due to invalid API key, but tests the flow)
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            # Mock failed models response
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.text = AsyncMock(return_value="Unauthorized")
            mock_session.get.return_value.__aenter__.return_value = mock_response

            result = await provider.connect()

            assert result is False
            assert provider.is_connected is False

        # Test disconnection
        result = await provider.disconnect()
        assert result is True

    @pytest.mark.asyncio
    async def test_llm_response_generation_integration(self, llm_manager):
        """Test LLM response generation integration."""
        # Setup mock providers
        mock_provider = AsyncMock()
        mock_provider.is_connected = True
        mock_provider.generate_response.return_value = "Test response from LLM"

        llm_manager.providers["openai"] = mock_provider

        # Test response generation
        messages = [Message(content="Hello", role="user")]
        context = Context(
            session_id="test-session",
            user_id="test-user",
            message="Hello",
            message_type="chat"
        )

        response = await llm_manager.generate_response(messages, context)

        assert response == "Test response from LLM"
        mock_provider.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_llm_fallback_integration(self, llm_manager):
        """Test LLM fallback integration."""
        # Setup mock providers
        mock_provider1 = AsyncMock()
        mock_provider1.is_connected = True
        mock_provider1.generate_response.side_effect = Exception("Provider 1 failed")

        mock_provider2 = AsyncMock()
        mock_provider2.is_connected = True
        mock_provider2.generate_response.return_value = "Fallback response"

        llm_manager.providers["openai"] = mock_provider1
        llm_manager.providers["anthropic"] = mock_provider2

        # Test fallback
        messages = [Message(content="Hello", role="user")]

        response = await llm_manager.generate_response(messages)

        assert response == "Fallback response"
        mock_provider1.generate_response.assert_called_once()
        mock_provider2.generate_response.assert_called_once()


class TestMCPIntegration:
    """Integration tests for MCP components."""

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
    async def test_mcp_manager_lifecycle(self, mcp_manager):
        """Test complete MCP manager lifecycle."""
        # Test start
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

        # Test stop
        with patch.object(mcp_manager, 'remove_server') as mock_remove_server:
            mock_remove_server.return_value = True

            await mcp_manager.stop()

            assert mock_remove_server.call_count == 2
            assert mcp_manager.health_check_task is None

    @pytest.mark.asyncio
    async def test_mcp_factory_integration(self):
        """Test MCP factory integration."""
        # Test transport registration
        class TestTransport(STDIOTransport):
            pass

        MCPFactory.register_transport("test_transport", TestTransport)

        # Verify registration
        transports = MCPFactory.get_available_transports()
        assert "test_transport" in transports

        # Test transport creation
        config = {
            "command": "echo",
            "args": ["test"]
        }

        transport = MCPFactory.create_transport("test_transport", config)
        assert isinstance(transport, TestTransport)

        # Cleanup
        del MCPFactory._transports["test_transport"]

    @pytest.mark.asyncio
    async def test_mcp_server_integration(self):
        """Test MCP server integration."""
        config = {
            "name": "test_server",
            "type": "file_system",
            "transport": "stdio",
            "command": "echo",
            "args": ["test"]
        }

        server = GenericMCPServer(config)

        # Test connection (will fail due to invalid command, but tests the flow)
        with patch('mcp.mcp_factory.MCPFactory.create_transport_from_config') as mock_create_transport:
            mock_transport = AsyncMock()
            mock_transport.connect.return_value = False
            mock_create_transport.return_value = mock_transport

            result = await server.connect()

            assert result is False
            assert server.is_connected is False

        # Test disconnection
        result = await server.disconnect()
        assert result is True

    @pytest.mark.asyncio
    async def test_mcp_tool_calling_integration(self, mcp_manager):
        """Test MCP tool calling integration."""
        # Setup mock servers
        mock_server = AsyncMock()
        mock_server.is_connected = True
        mock_server.call_tool.return_value = {"result": "Tool executed successfully"}

        mcp_manager.servers["file_server"] = mock_server

        # Test tool calling
        result = await mcp_manager.call_tool("test_tool", {"param": "value"})

        assert result == {"result": "Tool executed successfully"}
        mock_server.call_tool.assert_called_once_with("test_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_mcp_server_discovery_integration(self, mcp_manager):
        """Test MCP server discovery integration."""
        # Setup mock servers
        mock_server1 = AsyncMock()
        mock_server1.list_tools.return_value = [
            {"name": "tool1", "description": "First tool"},
            {"name": "tool2", "description": "Second tool"}
        ]

        mock_server2 = AsyncMock()
        mock_server2.list_tools.return_value = [
            {"name": "tool3", "description": "Third tool"}
        ]

        mcp_manager.servers["file_server"] = mock_server1
        mcp_manager.servers["db_server"] = mock_server2

        # Test tool discovery
        all_tools = await mcp_manager.get_all_tools()

        assert "file_server" in all_tools
        assert "db_server" in all_tools
        assert len(all_tools["file_server"]) == 2
        assert len(all_tools["db_server"]) == 1


class TestTransportIntegration:
    """Integration tests for transport components."""

    @pytest.mark.asyncio
    async def test_stdio_transport_integration(self):
        """Test STDIO transport integration."""
        config = {
            "command": "echo",
            "args": ["test"],
            "working_dir": "/tmp"
        }

        transport = STDIOTransport(config)

        # Test connection (will fail due to invalid command, but tests the flow)
        with patch('subprocess.Popen') as mock_popen:
            mock_popen.side_effect = Exception("Command not found")

            result = await transport.connect()

            assert result is False
            assert transport.is_connected is False

        # Test disconnection
        result = await transport.disconnect()
        assert result is True

    @pytest.mark.asyncio
    async def test_http_transport_integration(self):
        """Test HTTP transport integration."""
        config = {
            "base_url": "http://localhost:8080",
            "api_key": "test_key",
            "timeout": 30
        }

        transport = HTTPTransport(config)

        # Test connection (will fail due to invalid URL, but tests the flow)
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            with patch.object(transport, 'validate_connection') as mock_validate:
                mock_validate.return_value = False

                result = await transport.connect()

                assert result is False
                assert transport.is_connected is False

        # Test disconnection
        result = await transport.disconnect()
        assert result is True

    @pytest.mark.asyncio
    async def test_transport_message_formatting_integration(self):
        """Test transport message formatting integration."""
        # Test STDIO transport
        stdio_config = {"command": "echo"}
        stdio_transport = STDIOTransport(stdio_config)

        method = "test_method"
        params = {"param1": "value1"}
        request_id = "test-123"

        formatted = stdio_transport.format_message(method, params, request_id)

        assert formatted["jsonrpc"] == "2.0"
        assert formatted["id"] == "test-123"
        assert formatted["method"] == "test_method"
        assert formatted["params"] == {"param1": "value1"}

        # Test HTTP transport
        http_config = {"base_url": "http://localhost:8080"}
        http_transport = HTTPTransport(http_config)

        formatted = http_transport.format_message(method, params, request_id)

        assert formatted["jsonrpc"] == "2.0"
        assert formatted["id"] == "test-123"
        assert formatted["method"] == "test_method"
        assert formatted["params"] == {"param1": "value1"}


class TestLLMMCPCrossIntegration:
    """Cross-integration tests between LLM and MCP components."""

    @pytest.mark.asyncio
    async def test_llm_mcp_manager_integration(self):
        """Test integration between LLM and MCP managers."""
        # Create managers
        llm_config = {
            "default_provider": "openai",
            "providers": {
                "openai": {
                    "name": "openai",
                    "model": "gpt-3.5-turbo",
                    "api_key": "test_key"
                }
            }
        }

        mcp_config = {
            "servers": {
                "file_server": {
                    "name": "file_server",
                    "type": "file_system",
                    "transport": "stdio",
                    "command": "echo"
                }
            }
        }

        llm_manager = LLMManager(llm_config)
        mcp_manager = MCPManager(mcp_config)

        # Test concurrent operations
        with patch.object(llm_manager, 'add_provider') as mock_add_provider:
            with patch.object(mcp_manager, 'add_server') as mock_add_server:
                mock_add_provider.return_value = True
                mock_add_server.return_value = True

                # Start both managers concurrently
                await asyncio.gather(
                    llm_manager.start(),
                    mcp_manager.start()
                )

                assert mock_add_provider.call_count == 1
                assert mock_add_server.call_count == 1

                # Stop both managers
                await asyncio.gather(
                    llm_manager.stop(),
                    mcp_manager.stop()
                )

    @pytest.mark.asyncio
    async def test_factory_integration(self):
        """Test integration between LLM and MCP factories."""
        # Test LLM factory
        llm_providers = LLMFactory.get_available_providers()
        assert "openai" in llm_providers

        # Test MCP factory
        mcp_transports = MCPFactory.get_available_transports()
        assert "stdio" in mcp_transports
        assert "http" in mcp_transports

        # Test provider creation
        llm_config = {
            "name": "openai",
            "model": "gpt-3.5-turbo",
            "api_key": "test_key"
        }

        llm_provider = LLMFactory.create_provider("openai", llm_config)
        assert isinstance(llm_provider, OpenAIProvider)

        # Test transport creation
        mcp_config = {
            "command": "echo",
            "args": ["test"]
        }

        mcp_transport = MCPFactory.create_transport("stdio", mcp_config)
        assert isinstance(mcp_transport, STDIOTransport)

    @pytest.mark.asyncio
    async def test_configuration_integration(self):
        """Test configuration integration for LLM and MCP."""
        # Setup logging
        setup_logging(level="INFO", console_output=False)

        # Create configuration manager
        config_manager = ConfigurationManager()

        # Test LLM configuration
        llm_config = config_manager.get_llm_config()
        assert isinstance(llm_config, dict)

        # Test MCP configuration
        mcp_config = config_manager.get_mcp_config()
        assert isinstance(mcp_config, dict)

        # Test configuration validation
        assert config_manager.validate_configuration() is True


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    @pytest.mark.asyncio
    async def test_llm_error_handling_integration(self):
        """Test LLM error handling integration."""
        llm_config = {
            "default_provider": "openai",
            "providers": {
                "openai": {
                    "name": "openai",
                    "model": "gpt-3.5-turbo",
                    "api_key": "test_key"
                }
            }
        }

        llm_manager = LLMManager(llm_config)

        # Test with no providers
        with pytest.raises(RuntimeError, match="No LLM providers available"):
            await llm_manager.generate_response([Message(content="test", role="user")])

        # Test with failing provider
        mock_provider = AsyncMock()
        mock_provider.is_connected = True
        mock_provider.generate_response.side_effect = Exception("Provider failed")

        llm_manager.providers["openai"] = mock_provider

        with pytest.raises(RuntimeError, match="All LLM providers failed"):
            await llm_manager.generate_response([Message(content="test", role="user")])

    @pytest.mark.asyncio
    async def test_mcp_error_handling_integration(self):
        """Test MCP error handling integration."""
        mcp_config = {
            "servers": {
                "file_server": {
                    "name": "file_server",
                    "type": "file_system",
                    "transport": "stdio",
                    "command": "echo"
                }
            }
        }

        mcp_manager = MCPManager(mcp_config)

        # Test with no servers
        with pytest.raises(RuntimeError, match="No MCP servers available"):
            await mcp_manager.call_tool("test_tool", {})

        # Test with failing server
        mock_server = AsyncMock()
        mock_server.is_connected = True
        mock_server.call_tool.side_effect = Exception("Server failed")

        mcp_manager.servers["file_server"] = mock_server

        with pytest.raises(RuntimeError, match="All MCP servers failed"):
            await mcp_manager.call_tool("test_tool", {})

    @pytest.mark.asyncio
    async def test_transport_error_handling_integration(self):
        """Test transport error handling integration."""
        # Test STDIO transport errors
        stdio_config = {"command": "nonexistent_command"}
        stdio_transport = STDIOTransport(stdio_config)

        with patch('subprocess.Popen') as mock_popen:
            mock_popen.side_effect = FileNotFoundError("Command not found")

            result = await stdio_transport.connect()
            assert result is False

        # Test HTTP transport errors
        http_config = {"base_url": "http://invalid-url"}
        http_transport = HTTPTransport(http_config)

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session_class.side_effect = Exception("Connection failed")

            result = await http_transport.connect()
            assert result is False 