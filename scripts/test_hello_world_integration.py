#!/usr/bin/env python3
"""
Integration test for Hello World HTTP MCP Server with Chatbot

This script tests the integration between the chatbot and the Hello World HTTP MCP server.
It verifies that the chatbot can discover, connect to, and use the MCP server.

Usage: python scripts/test_hello_world_integration.py
"""

import json
import sys
import asyncio
import subprocess
import time
from typing import Dict, Any, Optional
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    # Add src to path for imports
    sys.path.insert(0, str(project_root / "src"))
    
    from mcp.mcp_manager import MCPManager
    from utils.config_manager import ConfigurationManager
    from utils.logger import LoggerMixin
except ImportError as e:
    print(f"Error: Could not import chatbot modules: {e}")
    print("Make sure you're running from the project root and the virtual environment is activated.")
    sys.exit(1)


class HelloWorldIntegrationTester(LoggerMixin):
    """Integration tester for Hello World MCP Server with Chatbot."""
    
    def __init__(self):
        """Initialize the integration tester."""
        self.config_manager = ConfigurationManager()
        self.mcp_manager = None
        self.server_process = None
        
    async def setup(self):
        """Setup the test environment."""
        print("🔧 Setting up integration test environment...")
        
        # Get configuration
        config = self.config_manager.get_all_config()
        
        # Initialize MCP manager
        self.mcp_manager = MCPManager(config.get("mcp", {}))
        
        print("✅ Test environment setup complete")
    
    def start_hello_world_server(self) -> bool:
        """Start the Hello World HTTP MCP server."""
        print("🚀 Starting Hello World HTTP MCP Server...")
        
        try:
            # Start the server in a subprocess
            cmd = [
                sys.executable,
                "mcp_servers/hello_world_http_server.py",
                "--host", "0.0.0.0",
                "--port", "8081"
            ]
            
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a moment for the server to start
            time.sleep(3)
            
            # Check if the server is running
            if self.server_process.poll() is None:
                print("✅ Hello World HTTP MCP Server started successfully")
                return True
            else:
                stdout, stderr = self.server_process.communicate()
                print(f"❌ Failed to start server. stdout: {stdout}")
                print(f"❌ stderr: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False
    
    def stop_hello_world_server(self):
        """Stop the Hello World HTTP MCP server."""
        if self.server_process:
            print("🛑 Stopping Hello World HTTP MCP Server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
                print("✅ Server stopped successfully")
            except subprocess.TimeoutExpired:
                print("⚠️  Server didn't stop gracefully, forcing termination")
                self.server_process.kill()
    
    async def test_mcp_discovery(self) -> bool:
        """Test MCP server discovery."""
        print("\n=== Testing MCP Server Discovery ===")
        try:
            # Start MCP manager
            await self.mcp_manager.start()
            
            # List servers
            servers = self.mcp_manager.list_servers()
            
            print(f"Found {len(servers)} MCP servers:")
            for server_name in servers:
                server = self.mcp_manager.get_server(server_name)
                if server:
                    print(f"  - {server_name} ({server.server_type})")
            
            # Check if Hello World server is available
            if "hello_world_http" in servers:
                print("✅ Hello World MCP server discovered")
                return True
            else:
                print("❌ Hello World MCP server not discovered")
                return False
                
        except Exception as e:
            print(f"❌ MCP discovery error: {e}")
            return False
    
    async def test_mcp_connection(self) -> bool:
        """Test MCP server connection."""
        print("\n=== Testing MCP Server Connection ===")
        try:
            # Get Hello World server
            hello_world_server = self.mcp_manager.get_server("hello_world_http")
            
            if hello_world_server and hello_world_server.is_connected:
                print("✅ Successfully connected to Hello World MCP server")
                return True
            else:
                print("❌ Failed to connect to Hello World MCP server")
                return False
                
        except Exception as e:
            print(f"❌ MCP connection error: {e}")
            return False
    
    async def test_mcp_tools(self) -> bool:
        """Test MCP server tools."""
        print("\n=== Testing MCP Server Tools ===")
        try:
            # Get Hello World server
            hello_world_server = self.mcp_manager.get_server("hello_world_http")
            
            if not hello_world_server:
                print("❌ Hello World server not available")
                return False
            
            # List tools
            tools = await hello_world_server.list_tools()
            print(f"Available tools: {[tool['name'] for tool in tools]}")
            
            # Test hello_world tool
            result = await hello_world_server.call_tool("hello_world", {
                "name": "Integration Tester",
                "language": "en"
            })
            
            if result and "content" in result:
                print("✅ Hello World tool call successful")
                print(f"Response: {result['content']}")
                return True
            else:
                print("❌ Hello World tool call failed")
                return False
                
        except Exception as e:
            print(f"❌ MCP tools error: {e}")
            return False
    
    async def test_mcp_resources(self) -> bool:
        """Test MCP server resources."""
        print("\n=== Testing MCP Server Resources ===")
        try:
            # Get Hello World server
            hello_world_server = self.mcp_manager.get_server("hello_world_http")
            
            if not hello_world_server:
                print("❌ Hello World server not available")
                return False
            
            # List resources
            resources = await hello_world_server.list_resources()
            print(f"Available resources: {[r['name'] for r in resources]}")
            
            if resources:
                print("✅ Resources listed successfully")
                return True
            else:
                print("❌ No resources found")
                return False
                
        except Exception as e:
            print(f"❌ MCP resources error: {e}")
            return False
    
    async def run_integration_tests(self) -> Dict[str, bool]:
        """Run all integration tests."""
        print("🚀 Starting Hello World MCP Server Integration Tests")
        
        results = {}
        
        try:
            # Setup
            await self.setup()
            
            # Start server
            results["server_start"] = self.start_hello_world_server()
            
            if not results["server_start"]:
                print("❌ Cannot proceed with tests - server failed to start")
                return results
            
            # Run tests
            results["mcp_discovery"] = await self.test_mcp_discovery()
            results["mcp_connection"] = await self.test_mcp_connection()
            results["mcp_tools"] = await self.test_mcp_tools()
            results["mcp_resources"] = await self.test_mcp_resources()
            
        except Exception as e:
            print(f"❌ Integration test error: {e}")
            results["general_error"] = False
        
        finally:
            # Cleanup
            self.stop_hello_world_server()
            if self.mcp_manager:
                await self.mcp_manager.stop()
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """Print test summary."""
        print("\n" + "="*50)
        print("INTEGRATION TEST SUMMARY")
        print("="*50)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All integration tests passed! The Hello World MCP Server is fully integrated.")
        else:
            print("⚠️  Some integration tests failed. Please check the configuration and server setup.")


async def main():
    """Main integration test function."""
    tester = HelloWorldIntegrationTester()
    
    try:
        results = await tester.run_integration_tests()
        tester.print_summary(results)
        
        # Exit with appropriate code
        if all(results.values()):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        tester.stop_hello_world_server()
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        tester.stop_hello_world_server()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 