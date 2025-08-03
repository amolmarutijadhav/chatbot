# Hello World HTTP MCP Server

A simple HTTP-based MCP (Model Context Protocol) server for testing connectivity and configuration with the intelligent chatbot.

## Overview

The Hello World HTTP MCP Server is designed as a QA testing tool to verify:
- MCP protocol implementation
- HTTP transport connectivity
- Tool and resource discovery
- Basic MCP functionality

## Features

### Available Tools

1. **hello_world** - Returns a simple Hello World message
   - Parameters:
     - `name` (optional): Name to greet (default: "World")
     - `language` (optional): Language for greeting (en, es, fr, de)

2. **echo** - Echo back the input message
   - Parameters:
     - `message` (required): Message to echo back

3. **ping** - Simple ping test for connectivity
   - Parameters:
     - `data` (optional): Optional data to include in ping response

4. **get_server_info** - Get server information and status
   - Parameters: None

### Available Resources

- **Server Information**: Basic server information and status

## Installation

### Prerequisites

```bash
pip install fastapi uvicorn
```

### Running the Server

```bash
# Basic usage (default: localhost:8081)
python mcp_servers/hello_world_http_server.py

# Custom host and port
python mcp_servers/hello_world_http_server.py --host 0.0.0.0 --port 8081
```

## Configuration

The server is configured in `config/chatbot_config.yaml`:

```yaml
mcp:
  servers:
    hello_world_http:
      name: "Hello World HTTP Server"
      type: "hello_world"
      enabled: true
      transport:
        type: "http"
        base_url: "http://localhost:8081"
        timeout: 30
        health_check_endpoint: "/health"
        mcp_endpoint: "/mcp"
```

## Testing

### 1. Basic Server Test

Test the server directly:

```bash
python scripts/test_hello_world_mcp.py
```

This will test:
- Health check endpoint
- Root endpoint
- MCP protocol methods
- All available tools

### 2. Integration Test

Test integration with the chatbot:

```bash
python scripts/test_hello_world_integration.py
```

This will test:
- Server startup
- MCP discovery
- Connection establishment
- Tool calls
- Resource listing

### 3. Manual Testing

You can also test manually using curl:

```bash
# Health check
curl http://localhost:8081/health

# Root endpoint
curl http://localhost:8081/

# MCP initialize
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": "1", "method": "initialize", "params": {}}'

# List tools
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": "2", "method": "tools/list", "params": {}}'

# Call hello_world tool
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": "3", "method": "tools/call", "params": {"name": "hello_world", "arguments": {"name": "Test User", "language": "en"}}}'
```

## API Endpoints

### Health Check
- **GET** `/health`
- Returns server health status

### Root
- **GET** `/`
- Returns basic server information

### MCP Protocol
- **POST** `/mcp`
- Handles all MCP protocol requests

## MCP Protocol Support

The server implements the following MCP methods:

- `initialize` - Initialize the MCP connection
- `tools/list` - List available tools
- `tools/call` - Call a specific tool
- `resources/list` - List available resources

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using the port
   netstat -an | grep 8081
   
   # Use a different port
   python mcp_servers/hello_world_http_server.py --port 8082
   ```

2. **Dependencies missing**
   ```bash
   pip install fastapi uvicorn
   ```

3. **Server not starting**
   - Check if Python path is correct
   - Verify all dependencies are installed
   - Check firewall settings

### Logs

The server outputs logs to stdout. Look for:
- Server startup messages
- Request/response logs
- Error messages

## Development

### Adding New Tools

To add a new tool:

1. Add tool definition to `handle_tools_list()`
2. Add tool implementation method
3. Add tool call handler in `handle_tools_call()`

### Adding New Resources

To add a new resource:

1. Add resource definition to `handle_resources_list()`
2. Implement resource handling logic

## Security Notes

- This is a testing server and should not be used in production
- No authentication is implemented
- Server binds to all interfaces by default (0.0.0.0)
- Consider firewall rules for production use

## License

This server is part of the intelligent chatbot project and follows the same license terms. 