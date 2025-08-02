# MCP Server Setup Guide

This guide explains how to set up and use the MCP (Model Context Protocol) server with your chatbot.

## What is MCP?

MCP (Model Context Protocol) allows your chatbot to interact with external tools and resources. The MCP server provides a standardized way for the chatbot to:

- Access file systems
- Execute commands
- Query databases
- Interact with APIs
- And much more

## Included MCP Server

We've included a **File System MCP Server** that provides basic file operations:

### Available Tools

1. **`list_files`** - List files in a directory
   - Parameters: `path` (optional), `pattern` (optional)
   - Example: List all Python files in current directory

2. **`read_file`** - Read contents of a file
   - Parameters: `path` (required), `encoding` (optional, default: utf-8)
   - Example: Read a configuration file

3. **`file_info`** - Get information about a file
   - Parameters: `path` (required)
   - Example: Get file size, creation date, permissions

4. **`search_files`** - Search for files by pattern
   - Parameters: `pattern` (required), `recursive` (optional, default: false)
   - Example: Find all Python files recursively

## Configuration

The MCP server is configured in `config/chatbot_config.yaml`:

```yaml
mcp:
  servers:
    file_system_stdio:
      name: "File System Server (STDIO)"
      enabled: true
      transport:
        type: "stdio"
        command: "python"
        args: ["mcp_servers/filesystem_server.py"]
        working_directory: "."
        environment:
          MCP_FS_ROOT: "."
          PYTHONPATH: "."
        timeout: 30
```

### Configuration Options

- **`enabled`**: Set to `true` to enable the server
- **`command`**: The command to start the server
- **`args`**: Arguments passed to the command
- **`working_directory`**: Working directory for the server
- **`environment`**: Environment variables for the server
- **`timeout`**: Request timeout in seconds

## Testing the MCP Server

### 1. Test Standalone Server

```bash
python scripts/test_mcp_server.py
```

This will test both the standalone server and the integrated server.

### 2. Test with Chatbot

```bash
# Demo mode
python src/main.py demo

# Interactive mode
python src/main.py interactive
```

## Using MCP in Conversations

Once the MCP server is running, your chatbot can use it to:

### List Files
```
User: "Show me the files in the current directory"
Assistant: I'll list the files for you.
[Uses MCP to call list_files tool]
```

### Read Files
```
User: "Read the README.md file"
Assistant: I'll read the README.md file for you.
[Uses MCP to call read_file tool]
```

### Search Files
```
User: "Find all Python files"
Assistant: I'll search for Python files in the project.
[Uses MCP to call search_files tool with pattern "*.py"]
```

## Security Considerations

The MCP server runs with the same permissions as the chatbot process. Be aware that:

1. **File Access**: The server can access any files the chatbot process can access
2. **Directory Scope**: The server is limited to the configured root directory
3. **Process Isolation**: The server runs as a separate process for isolation

## Troubleshooting

### Server Won't Start

1. **Check Python Path**: Ensure Python is in your PATH
2. **Check File Permissions**: Ensure the server file is executable
3. **Check Working Directory**: Ensure the working directory exists

### Connection Errors

1. **Check Configuration**: Verify the server is enabled in config
2. **Check Logs**: Look for error messages in the logs
3. **Test Standalone**: Run the standalone test first

### Tool Call Errors

1. **Check Parameters**: Ensure required parameters are provided
2. **Check File Paths**: Ensure file paths are relative to the root directory
3. **Check Permissions**: Ensure the chatbot has permission to access files

## Creating Custom MCP Servers

You can create your own MCP servers by:

1. **Implementing the Protocol**: Follow the MCP specification
2. **Adding to Configuration**: Add your server to the config file
3. **Testing**: Use the test script to verify functionality

### Example Custom Server

```python
#!/usr/bin/env python3
import json
import sys

class CustomMCPServer:
    def __init__(self):
        self.request_id = 0
    
    def send_response(self, result=None, error=None, id=None):
        response = {
            "jsonrpc": "2.0",
            "id": id
        }
        if error:
            response["error"] = {"code": -1, "message": error}
        else:
            response["result"] = result
        print(json.dumps(response), flush=True)
    
    def run(self):
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            
            try:
                request = json.loads(line.strip())
                # Handle your custom methods here
                pass
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    server = CustomMCPServer()
    server.run()
```

## Next Steps

1. **Explore Tools**: Try different MCP tools in conversations
2. **Add More Servers**: Create additional MCP servers for other functionality
3. **Integrate APIs**: Connect to external APIs through MCP
4. **Database Access**: Add database query capabilities
5. **System Commands**: Add ability to execute system commands

## Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP GitHub Repository](https://github.com/modelcontextprotocol)
- [MCP Server Examples](https://github.com/modelcontextprotocol/python-sdk) 