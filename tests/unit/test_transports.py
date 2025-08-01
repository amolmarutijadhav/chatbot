"""Unit tests for MCP transport classes."""

import pytest
import asyncio
import sys
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mcp.transports.base_transport import BaseTransport
from mcp.transports.stdio_transport import STDIOTransport
from mcp.transports.http_transport import HTTPTransport


class TestBaseTransport:
    """Test the abstract BaseTransport base class."""

    def test_base_transport_initialization(self):
        """Test BaseTransport initialization."""
        config = {
            "test_param": "test_value",
            "timeout": 30
        }

        # Create a concrete implementation for testing
        class TestTransport(BaseTransport):
            async def connect(self) -> bool:
                return True

            async def disconnect(self) -> bool:
                return True

            async def send_message(self, message: dict) -> dict:
                return {"result": "test_response"}

            async def receive_message(self) -> dict:
                return {"type": "test"}

        transport = TestTransport(config)

        assert transport.config == config
        assert transport.is_connected is False

    def test_format_message(self):
        """Test message formatting."""
        config = {"test": "config"}
        
        class TestTransport(BaseTransport):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_message(self, message: dict) -> dict: return {}
            async def receive_message(self) -> dict: return {}

        transport = TestTransport(config)

        method = "test_method"
        params = {"param1": "value1", "param2": "value2"}
        request_id = "test-123"

        formatted = transport.format_message(method, params, request_id)

        assert formatted["jsonrpc"] == "2.0"
        assert formatted["id"] == "test-123"
        assert formatted["method"] == "test_method"
        assert formatted["params"] == {"param1": "value1", "param2": "value2"}

    def test_parse_message_success(self):
        """Test successful message parsing."""
        config = {"test": "config"}
        
        class TestTransport(BaseTransport):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_message(self, message: dict) -> dict: return {}
            async def receive_message(self) -> dict: return {}

        transport = TestTransport(config)

        message_str = '{"jsonrpc": "2.0", "id": "test", "result": "success"}'
        parsed = transport.parse_message(message_str)

        assert parsed["jsonrpc"] == "2.0"
        assert parsed["id"] == "test"
        assert parsed["result"] == "success"

    def test_parse_message_invalid_json(self):
        """Test message parsing with invalid JSON."""
        config = {"test": "config"}
        
        class TestTransport(BaseTransport):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_message(self, message: dict) -> dict: return {}
            async def receive_message(self) -> dict: return {}

        transport = TestTransport(config)

        invalid_json = '{"invalid": json}'

        with pytest.raises(ValueError, match="Invalid JSON message"):
            transport.parse_message(invalid_json)

    def test_validate_response_success(self):
        """Test successful response validation."""
        config = {"test": "config"}
        
        class TestTransport(BaseTransport):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_message(self, message: dict) -> dict: return {}
            async def receive_message(self) -> dict: return {}

        transport = TestTransport(config)

        valid_response = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "result": "success"
        }

        assert transport.validate_response(valid_response) is True

    def test_validate_response_missing_jsonrpc(self):
        """Test response validation with missing jsonrpc."""
        config = {"test": "config"}
        
        class TestTransport(BaseTransport):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_message(self, message: dict) -> dict: return {}
            async def receive_message(self) -> dict: return {}

        transport = TestTransport(config)

        invalid_response = {
            "id": "test-123",
            "result": "success"
        }

        assert transport.validate_response(invalid_response) is False

    def test_validate_response_wrong_jsonrpc_version(self):
        """Test response validation with wrong jsonrpc version."""
        config = {"test": "config"}
        
        class TestTransport(BaseTransport):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_message(self, message: dict) -> dict: return {}
            async def receive_message(self) -> dict: return {}

        transport = TestTransport(config)

        invalid_response = {
            "jsonrpc": "1.0",
            "id": "test-123",
            "result": "success"
        }

        assert transport.validate_response(invalid_response) is False

    def test_validate_response_missing_id(self):
        """Test response validation with missing id."""
        config = {"test": "config"}
        
        class TestTransport(BaseTransport):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_message(self, message: dict) -> dict: return {}
            async def receive_message(self) -> dict: return {}

        transport = TestTransport(config)

        invalid_response = {
            "jsonrpc": "2.0",
            "result": "success"
        }

        assert transport.validate_response(invalid_response) is False

    def test_validate_response_with_error(self):
        """Test response validation with error."""
        config = {"test": "config"}
        
        class TestTransport(BaseTransport):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_message(self, message: dict) -> dict: return {}
            async def receive_message(self) -> dict: return {}

        transport = TestTransport(config)

        error_response = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "error": {"code": -1, "message": "Error"}
        }

        assert transport.validate_response(error_response) is False

    def test_validate_response_missing_result(self):
        """Test response validation with missing result."""
        config = {"test": "config"}
        
        class TestTransport(BaseTransport):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_message(self, message: dict) -> dict: return {}
            async def receive_message(self) -> dict: return {}

        transport = TestTransport(config)

        invalid_response = {
            "jsonrpc": "2.0",
            "id": "test-123"
        }

        assert transport.validate_response(invalid_response) is False

    def test_get_error_from_response(self):
        """Test extracting error from response."""
        config = {"test": "config"}
        
        class TestTransport(BaseTransport):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_message(self, message: dict) -> dict: return {}
            async def receive_message(self) -> dict: return {}

        transport = TestTransport(config)

        error_response = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "error": {"code": -1, "message": "Test error"}
        }

        error_msg = transport.get_error_from_response(error_response)
        assert error_msg == "Error -1: Test error"

    def test_get_error_from_response_no_error(self):
        """Test extracting error from response without error."""
        config = {"test": "config"}
        
        class TestTransport(BaseTransport):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_message(self, message: dict) -> dict: return {}
            async def receive_message(self) -> dict: return {}

        transport = TestTransport(config)

        valid_response = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "result": "success"
        }

        error_msg = transport.get_error_from_response(valid_response)
        assert error_msg is None

    def test_get_result_from_response(self):
        """Test extracting result from response."""
        config = {"test": "config"}
        
        class TestTransport(BaseTransport):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_message(self, message: dict) -> dict: return {}
            async def receive_message(self) -> dict: return {}

        transport = TestTransport(config)

        response = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "result": {"data": "test_data"}
        }

        result = transport.get_result_from_response(response)
        assert result == {"data": "test_data"}

    def test_get_result_from_response_no_result(self):
        """Test extracting result from response without result."""
        config = {"test": "config"}
        
        class TestTransport(BaseTransport):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def send_message(self, message: dict) -> dict: return {}
            async def receive_message(self) -> dict: return {}

        transport = TestTransport(config)

        response = {
            "jsonrpc": "2.0",
            "id": "test-123"
        }

        result = transport.get_result_from_response(response)
        assert result is None


class TestSTDIOTransport:
    """Test the STDIO transport implementation."""

    @pytest.fixture
    def stdio_config(self):
        return {
            "command": "echo",
            "args": ["test"],
            "working_dir": "/tmp",
            "env": {"TEST_VAR": "test_value"}
        }

    @pytest.fixture
    def stdio_transport(self, stdio_config):
        return STDIOTransport(stdio_config)

    @pytest.mark.asyncio
    async def test_stdio_transport_initialization(self, stdio_transport, stdio_config):
        """Test STDIO transport initialization."""
        assert stdio_transport.config == stdio_config
        assert stdio_transport.command == "echo"
        assert stdio_transport.args == ["test"]
        assert stdio_transport.working_dir == "/tmp"
        assert stdio_transport.env == {"TEST_VAR": "test_value"}
        assert stdio_transport.process is None
        assert stdio_transport.request_id == 0
        assert stdio_transport.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_success(self, stdio_transport):
        """Test successful connection via STDIO."""
        with patch('mcp.transports.stdio_transport.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None  # Process is alive
            mock_process.stdin = Mock()
            mock_process.stdout = Mock()
            mock_popen.return_value = mock_process

            result = await stdio_transport.connect()

            assert result is True
            assert stdio_transport.is_connected is True
            assert stdio_transport.process == mock_process
            mock_popen.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_no_command(self, stdio_config):
        """Test connection failure when no command is specified."""
        stdio_config["command"] = ""
        transport = STDIOTransport(stdio_config)

        result = await transport.connect()

        assert result is False
        assert transport.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_process_failure(self, stdio_transport):
        """Test connection failure due to process failure."""
        with patch('mcp.transports.stdio_transport.Popen') as mock_popen:
            mock_popen.side_effect = Exception("Process failed")

            result = await stdio_transport.connect()

            assert result is False
            assert stdio_transport.is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect_success(self, stdio_transport):
        """Test successful disconnection."""
        # First connect
        with patch('mcp.transports.stdio_transport.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process

            await stdio_transport.connect()

        # Then disconnect
        result = await stdio_transport.disconnect()

        assert result is True
        assert stdio_transport.is_connected is False
        assert stdio_transport.process is None

    @pytest.mark.asyncio
    async def test_disconnect_no_process(self, stdio_transport):
        """Test disconnection when no process exists."""
        result = await stdio_transport.disconnect()

        assert result is True
        assert stdio_transport.is_connected is False

    @pytest.mark.asyncio
    async def test_send_message_success(self, stdio_transport):
        """Test successful message sending."""
        # Setup connection
        with patch('mcp.transports.stdio_transport.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_process.stdin = Mock()
            mock_process.stdout = Mock()
            mock_process.stdout.readline.return_value = '{"jsonrpc": "2.0", "id": "test", "result": "success"}\n'
            mock_popen.return_value = mock_process

            await stdio_transport.connect()

        # Test message sending
        message = {"jsonrpc": "2.0", "id": "test", "method": "test_method", "params": {}}
        result = await stdio_transport.send_message(message)

        assert result["jsonrpc"] == "2.0"
        assert result["id"] == "test"
        assert result["result"] == "success"

    @pytest.mark.asyncio
    async def test_send_message_not_connected(self, stdio_transport):
        """Test message sending when not connected."""
        message = {"test": "message"}

        with pytest.raises(ConnectionError, match="STDIO transport not connected"):
            await stdio_transport.send_message(message)

    @pytest.mark.asyncio
    async def test_send_message_no_response(self, stdio_transport):
        """Test message sending with no response."""
        # Setup connection
        with patch('mcp.transports.stdio_transport.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_process.stdin = Mock()
            mock_process.stdout = Mock()
            mock_process.stdout.readline.return_value = ""  # No response
            mock_popen.return_value = mock_process

            await stdio_transport.connect()

        # Test message sending
        message = {"test": "message"}

        with pytest.raises(ConnectionError, match="No response from MCP server"):
            await stdio_transport.send_message(message)

    @pytest.mark.asyncio
    async def test_send_message_invalid_response(self, stdio_transport):
        """Test message sending with invalid response."""
        # Setup connection
        with patch('mcp.transports.stdio_transport.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_process.stdin = Mock()
            mock_process.stdout = Mock()
            mock_process.stdout.readline.return_value = '{"invalid": "response"}\n'
            mock_popen.return_value = mock_process

            await stdio_transport.connect()

        # Test message sending
        message = {"test": "message"}

        with pytest.raises(Exception, match="Invalid response from MCP server"):
            await stdio_transport.send_message(message)

    @pytest.mark.asyncio
    async def test_receive_message_success(self, stdio_transport):
        """Test successful message receiving."""
        # Setup connection
        with patch('mcp.transports.stdio_transport.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_process.stdout = Mock()
            mock_process.stdout.readline.return_value = '{"jsonrpc": "2.0", "id": "test", "result": "success"}\n'
            mock_popen.return_value = mock_process

            await stdio_transport.connect()

        # Test message receiving
        result = await stdio_transport.receive_message()

        assert result["jsonrpc"] == "2.0"
        assert result["id"] == "test"
        assert result["result"] == "success"

    @pytest.mark.asyncio
    async def test_receive_message_no_connection(self, stdio_transport):
        """Test message receiving when not connected."""
        result = await stdio_transport.receive_message()

        assert result is None

    @pytest.mark.asyncio
    async def test_receive_message_no_data(self, stdio_transport):
        """Test message receiving with no data."""
        # Setup connection
        with patch('mcp.transports.stdio_transport.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_process.stdout = Mock()
            mock_process.stdout.readline.return_value = ""  # No data
            mock_popen.return_value = mock_process

            await stdio_transport.connect()

        # Test message receiving
        result = await stdio_transport.receive_message()

        assert result is None

    def test_get_next_request_id(self, stdio_transport):
        """Test getting next request ID."""
        initial_id = stdio_transport.request_id

        request_id1 = stdio_transport.get_next_request_id()
        request_id2 = stdio_transport.get_next_request_id()

        assert request_id1 == str(initial_id + 1)
        assert request_id2 == str(initial_id + 2)

    def test_is_process_alive(self, stdio_transport):
        """Test checking if process is alive."""
        # Test with no process
        assert stdio_transport.is_process_alive() is False

        # Test with alive process
        with patch('mcp.transports.stdio_transport.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None  # Process is alive
            mock_popen.return_value = mock_process

            stdio_transport.process = mock_process
            assert stdio_transport.is_process_alive() is True

        # Test with dead process
        with patch('mcp.transports.stdio_transport.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = 0  # Process is dead
            mock_popen.return_value = mock_process

            stdio_transport.process = mock_process
            assert stdio_transport.is_process_alive() is False


class TestHTTPTransport:
    """Test the HTTP transport implementation."""

    @pytest.fixture
    def http_config(self):
        return {
            "base_url": "http://localhost:8080",
            "api_key": "test_key",
            "timeout": 30
        }

    @pytest.fixture
    def http_transport(self, http_config):
        return HTTPTransport(http_config)

    @pytest.mark.asyncio
    async def test_http_transport_initialization(self, http_transport, http_config):
        """Test HTTP transport initialization."""
        assert http_transport.config == http_config
        assert http_transport.base_url == "http://localhost:8080"
        assert http_transport.api_key == "test_key"
        assert http_transport.timeout == 30
        assert http_transport.session is None
        assert http_transport.request_id == 0
        assert http_transport.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_success(self, http_transport):
        """Test successful connection via HTTP."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            # Mock successful health check
            with patch.object(http_transport, 'validate_connection') as mock_validate:
                mock_validate.return_value = True

                result = await http_transport.connect()

                assert result is True
                assert http_transport.is_connected is True
                assert http_transport.session == mock_session

    @pytest.mark.asyncio
    async def test_connect_no_base_url(self, http_config):
        """Test connection failure when no base URL is specified."""
        http_config["base_url"] = ""
        transport = HTTPTransport(http_config)

        result = await transport.connect()

        assert result is False
        assert transport.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_validation_failure(self, http_transport):
        """Test connection failure due to validation failure."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            # Mock failed health check
            with patch.object(http_transport, 'validate_connection') as mock_validate:
                mock_validate.return_value = False

                result = await http_transport.connect()

                assert result is False
                assert http_transport.is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect_success(self, http_transport):
        """Test successful disconnection."""
        # First connect
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            with patch.object(http_transport, 'validate_connection') as mock_validate:
                mock_validate.return_value = True

                await http_transport.connect()

        # Then disconnect
        result = await http_transport.disconnect()

        assert result is True
        assert http_transport.is_connected is False
        assert http_transport.session is None

    @pytest.mark.asyncio
    async def test_send_message_success(self, http_transport):
        """Test successful message sending."""
        # Setup connection
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            # Mock successful POST request
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "jsonrpc": "2.0",
                "id": "test",
                "result": "success"
            })
            
            # Setup async context manager for session.post
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_session.post = Mock(return_value=mock_context)

            with patch.object(http_transport, 'validate_connection') as mock_validate:
                mock_validate.return_value = True

                await http_transport.connect()

        # Test message sending
        message = {"jsonrpc": "2.0", "id": "test", "method": "test_method", "params": {}}
        result = await http_transport.send_message(message)

        assert result["jsonrpc"] == "2.0"
        assert result["id"] == "test"
        assert result["result"] == "success"

    @pytest.mark.asyncio
    async def test_send_message_not_connected(self, http_transport):
        """Test message sending when not connected."""
        message = {"test": "message"}

        with pytest.raises(ConnectionError, match="HTTP transport not connected"):
            await http_transport.send_message(message)

    @pytest.mark.asyncio
    async def test_send_message_http_error(self, http_transport):
        """Test message sending with HTTP error."""
        # Setup connection
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            # Mock failed POST request
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.text = AsyncMock(return_value="Bad Request")
            
            # Setup async context manager for session.post
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_session.post = Mock(return_value=mock_context)

            with patch.object(http_transport, 'validate_connection') as mock_validate:
                mock_validate.return_value = True

                await http_transport.connect()

        # Test message sending
        message = {"test": "message"}

        with pytest.raises(Exception, match="HTTP error 400"):
            await http_transport.send_message(message)

    @pytest.mark.asyncio
    async def test_send_message_invalid_response(self, http_transport):
        """Test message sending with invalid response."""
        # Setup connection
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            # Mock successful POST request with invalid response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"invalid": "response"})
            
            # Setup async context manager for session.post
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_session.post = Mock(return_value=mock_context)

            with patch.object(http_transport, 'validate_connection') as mock_validate:
                mock_validate.return_value = True

                await http_transport.connect()

        # Test message sending
        message = {"test": "message"}

        with pytest.raises(Exception, match="Invalid response from MCP server"):
            await http_transport.send_message(message)

    @pytest.mark.asyncio
    async def test_receive_message(self, http_transport):
        """Test message receiving (should return None for HTTP transport)."""
        result = await http_transport.receive_message()

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_connection_success(self, http_transport):
        """Test successful connection validation."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            # Mock successful health check
            mock_response = AsyncMock()
            mock_response.status = 200
            
            # Setup async context manager for session.get
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_session.get = Mock(return_value=mock_context)

            http_transport.session = mock_session

            result = await http_transport.validate_connection()

            assert result is True

    @pytest.mark.asyncio
    async def test_validate_connection_no_session(self, http_transport):
        """Test connection validation with no session."""
        result = await http_transport.validate_connection()

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, http_transport):
        """Test connection validation failure."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            # Mock failed health check
            mock_response = AsyncMock()
            mock_response.status = 404
            
            # Setup async context manager for session.get
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_session.get = Mock(return_value=mock_context)

            http_transport.session = mock_session

            result = await http_transport.validate_connection()

            assert result is False

    def test_get_next_request_id(self, http_transport):
        """Test getting next request ID."""
        initial_id = http_transport.request_id

        request_id1 = http_transport.get_next_request_id()
        request_id2 = http_transport.get_next_request_id()

        assert request_id1 == str(initial_id + 1)
        assert request_id2 == str(initial_id + 2)

    @pytest.mark.asyncio
    async def test_get_server_info_success(self, http_transport):
        """Test successful server info retrieval."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            # Mock successful info request
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"name": "test_server", "version": "1.0"})
            
            # Setup async context manager for session.get
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_session.get = Mock(return_value=mock_context)

            http_transport.session = mock_session

            info = await http_transport.get_server_info()

            assert info["name"] == "test_server"
            assert info["version"] == "1.0"

    @pytest.mark.asyncio
    async def test_get_server_info_no_session(self, http_transport):
        """Test server info retrieval with no session."""
        info = await http_transport.get_server_info()

        assert info == {}

    @pytest.mark.asyncio
    async def test_get_server_info_failure(self, http_transport):
        """Test server info retrieval failure."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            # Mock failed info request
            mock_response = AsyncMock()
            mock_response.status = 404
            
            # Setup async context manager for session.get
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_session.get = Mock(return_value=mock_context)

            http_transport.session = mock_session

            info = await http_transport.get_server_info()

            assert info == {} 