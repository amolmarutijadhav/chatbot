#!/usr/bin/env python3
"""
Test script to verify MCP server functionality.
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config_manager import ConfigurationManager
from utils.logger import setup_logging, get_logger
from mcp.mcp_manager import MCPManager


async def test_mcp_server():
    """Test MCP server functionality."""
    logger = get_logger(__name__)
    
    print("🔧 Testing MCP Server Configuration...")
    print("=" * 50)
    
    # Initialize configuration
    config_manager = ConfigurationManager()
    
    # Setup logging
    logging_config = config_manager.get("logging", {})
    # Fix parameter names for setup_logging
    if "file" in logging_config:
        logging_config["log_file"] = logging_config.pop("file")
    logging_config.pop("format", None)
    setup_logging(**logging_config)
    
    # Get MCP configuration
    mcp_config = config_manager.get_mcp_config()
    print(f"✅ MCP Configuration loaded")
    
    # Check if any servers are enabled
    servers = mcp_config.get("servers", {})
    enabled_servers = [name for name, config in servers.items() if config.get("enabled", False)]
    
    if not enabled_servers:
        print("❌ No MCP servers are enabled!")
        print("Enable a server in config/chatbot_config.yaml")
        return False
    
    print(f"✅ Enabled MCP servers: {enabled_servers}")
    
    # Test MCP Manager
    try:
        print("\n🔧 Testing MCP Manager...")
        mcp_manager = MCPManager(mcp_config)
        await mcp_manager.start()
        
        print("✅ MCP Manager started successfully")
        
        # Get connected servers
        connected_servers = mcp_manager.servers
        print(f"✅ Connected servers: {list(connected_servers.keys())}")
        
        if not connected_servers:
            print("❌ No servers connected!")
            return False
        
        # Test each connected server
        for server_name, server in connected_servers.items():
            print(f"\n🧪 Testing server: {server_name}")
            
            # Test capabilities
            capabilities = await server.get_capabilities()
            print(f"   Capabilities: {capabilities}")
            
            # Test tools list
            tools = await server.list_tools()
            print(f"   Available tools: {len(tools)}")
            for tool in tools:
                print(f"     - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
            
            # Test file system operations if available
            if "list_files" in [tool.get("name") for tool in tools]:
                print("\n   📁 Testing file system operations...")
                
                # List files in current directory
                try:
                    result = await server.call_tool("list_files", {"path": "."})
                    files = result.get("files", [])
                    print(f"     Files in current directory: {len(files)}")
                    for file in files[:5]:  # Show first 5 files
                        print(f"       - {file.get('name')} ({file.get('type')})")
                    if len(files) > 5:
                        print(f"       ... and {len(files) - 5} more")
                except Exception as e:
                    print(f"     ❌ Error listing files: {e}")
                
                # Test file info
                try:
                    result = await server.call_tool("file_info", {"path": "README.md"})
                    print(f"     README.md info: {result.get('size', 'N/A')} bytes")
                except Exception as e:
                    print(f"     ❌ Error getting file info: {e}")
        
        await mcp_manager.stop()
        print("✅ MCP Manager stopped successfully")
        
    except Exception as e:
        print(f"❌ Error testing MCP Manager: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All MCP server tests passed successfully!")
    print("Your chatbot is ready to use with real MCP functionality.")
    return True


async def test_standalone_server():
    """Test the MCP server standalone."""
    print("\n🔧 Testing Standalone MCP Server...")
    print("=" * 30)
    
    import subprocess
    import time
    
    try:
        # Start the server
        server_path = "mcp_servers/filesystem_server.py"
        if not os.path.exists(server_path):
            print(f"❌ Server file not found: {server_path}")
            return False
        
        print(f"✅ Server file found: {server_path}")
        
        # Test server startup
        # Use virtual environment Python if available (cross-platform)
        if os.path.exists(".venv/Scripts/python.exe"):
            python_executable = ".venv/Scripts/python.exe"  # Windows
        elif os.path.exists(".venv/bin/python"):
            python_executable = ".venv/bin/python"  # Linux/Mac
        else:
            python_executable = sys.executable  # Fallback to system Python
        process = subprocess.Popen(
            [python_executable, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="."
        )
        
        # Give it a moment to start
        time.sleep(1)
        
        if process.poll() is not None:
            print("❌ Server failed to start")
            stderr = process.stderr.read()
            print(f"Error: {stderr}")
            return False
        
        print("✅ Server started successfully")
        
        # Test basic communication
        test_request = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # Send request
        request_str = json.dumps(test_request) + "\n"
        process.stdin.write(request_str)
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            if "result" in response:
                print("✅ Server responded correctly")
                server_info = response["result"].get("serverInfo", {})
                print(f"   Server: {server_info.get('name')} v{server_info.get('version')}")
            else:
                print("❌ Server returned error")
                print(f"   Error: {response.get('error', {})}")
        else:
            print("❌ No response from server")
        
        # Clean up
        process.terminate()
        process.wait(timeout=5)
        print("✅ Server stopped successfully")
        
    except Exception as e:
        print(f"❌ Error testing standalone server: {e}")
        return False
    
    return True


async def main():
    """Main function."""
    try:
        print("🚀 MCP Server Test Suite")
        print("=" * 50)
        
        # Test standalone server first
        standalone_success = await test_standalone_server()
        
        # Test integrated server
        integrated_success = await test_mcp_server()
        
        if standalone_success and integrated_success:
            print("\n🎉 All MCP tests passed!")
            print("\n🚀 You can now run your chatbot with MCP support:")
            print("   python src/main.py demo")
            print("   python src/main.py interactive")
            print("   python src/api_main.py")
        else:
            print("\n❌ Some MCP tests failed. Please check the configuration.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 