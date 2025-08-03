#!/usr/bin/env python3
"""
Hello World MCP Server Example

This example demonstrates how to use the Hello World HTTP MCP server
with the intelligent chatbot system.

Usage: python examples/hello_world_mcp_example.py
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from mcp.mcp_manager import MCPManager
from utils.config_manager import ConfigurationManager
from utils.logger import LoggerMixin


class HelloWorldMCPExample(LoggerMixin):
    """Example demonstrating Hello World MCP server usage."""
    
    def __init__(self):
        """Initialize the example."""
        self.config_manager = ConfigurationManager()
        self.mcp_manager = None
        
    async def setup(self):
        """Setup the example environment."""
        print("🔧 Setting up Hello World MCP Example...")
        
        # Get configuration
        config = self.config_manager.get_all_config()
        
        # Initialize MCP manager
        self.mcp_manager = MCPManager(config.get("mcp", {}))
        
        # Start MCP manager
        await self.mcp_manager.start()
        
        print("✅ Example environment setup complete")
    
    async def demonstrate_hello_world_tool(self):
        """Demonstrate the hello_world tool."""
        print("\n=== Hello World Tool Demo ===")
        
        try:
            # Get Hello World server
            hello_world_server = self.mcp_manager.get_server("hello_world_http")
            
            if not hello_world_server:
                print("❌ Hello World server not available")
                return False
            
            # Test different languages
            languages = ["en", "es", "fr", "de"]
            names = ["Alice", "Bob", "Charlie"]
            
            for language in languages:
                for name in names:
                    result = await hello_world_server.call_tool("hello_world", {
                        "name": name,
                        "language": language
                    })
                    
                    if result and "content" in result:
                        greeting = result["content"][0]["text"]
                        print(f"  {greeting}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error demonstrating hello_world tool: {e}")
            return False
    
    async def demonstrate_echo_tool(self):
        """Demonstrate the echo tool."""
        print("\n=== Echo Tool Demo ===")
        
        try:
            # Get Hello World server
            hello_world_server = self.mcp_manager.get_server("hello_world_http")
            
            if not hello_world_server:
                print("❌ Hello World server not available")
                return False
            
            # Test echo with different messages
            messages = [
                "Hello from the chatbot!",
                "Testing MCP integration",
                "This is a test message",
                "MCP servers are working!"
            ]
            
            for message in messages:
                result = await hello_world_server.call_tool("echo", {
                    "message": message
                })
                
                if result and "content" in result:
                    echo_response = result["content"][0]["text"]
                    print(f"  {echo_response}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error demonstrating echo tool: {e}")
            return False
    
    async def demonstrate_ping_tool(self):
        """Demonstrate the ping tool."""
        print("\n=== Ping Tool Demo ===")
        
        try:
            # Get Hello World server
            hello_world_server = self.mcp_manager.get_server("hello_world_http")
            
            if not hello_world_server:
                print("❌ Hello World server not available")
                return False
            
            # Test ping with different data
            test_data = [
                "connectivity_test",
                "performance_test",
                "integration_test",
                "final_test"
            ]
            
            for data in test_data:
                result = await hello_world_server.call_tool("ping", {
                    "data": data
                })
                
                if result and "content" in result:
                    ping_response = result["content"][0]["text"]
                    print(f"  {ping_response}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error demonstrating ping tool: {e}")
            return False
    
    async def demonstrate_server_info_tool(self):
        """Demonstrate the get_server_info tool."""
        print("\n=== Server Info Tool Demo ===")
        
        try:
            # Get Hello World server
            hello_world_server = self.mcp_manager.get_server("hello_world_http")
            
            if not hello_world_server:
                print("❌ Hello World server not available")
                return False
            
            # Get server information
            result = await hello_world_server.call_tool("get_server_info", {})
            
            if result and "content" in result:
                server_info = result["content"][0]["text"]
                print(f"  {server_info}")
                return True
            else:
                print("❌ Failed to get server info")
                return False
                
        except Exception as e:
            print(f"❌ Error demonstrating server info tool: {e}")
            return False
    
    async def demonstrate_all_tools(self):
        """Demonstrate all available tools."""
        print("\n=== All Tools Demo ===")
        
        try:
            # Get Hello World server
            hello_world_server = self.mcp_manager.get_server("hello_world_http")
            
            if not hello_world_server:
                print("❌ Hello World server not available")
                return False
            
            # List all tools
            tools = await hello_world_server.list_tools()
            print(f"Available tools: {[tool['name'] for tool in tools]}")
            
            # Call each tool
            for tool in tools:
                tool_name = tool['name']
                print(f"\n  Testing tool: {tool_name}")
                
                if tool_name == "hello_world":
                    result = await hello_world_server.call_tool(tool_name, {
                        "name": "Demo User",
                        "language": "en"
                    })
                elif tool_name == "echo":
                    result = await hello_world_server.call_tool(tool_name, {
                        "message": f"Testing {tool_name} tool"
                    })
                elif tool_name == "ping":
                    result = await hello_world_server.call_tool(tool_name, {
                        "data": f"demo_{tool_name}"
                    })
                elif tool_name == "get_server_info":
                    result = await hello_world_server.call_tool(tool_name, {})
                else:
                    print(f"    ⚠️  Unknown tool: {tool_name}")
                    continue
                
                if result and "content" in result:
                    response = result["content"][0]["text"]
                    print(f"    Response: {response}")
                else:
                    print(f"    ❌ No response from {tool_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error demonstrating all tools: {e}")
            return False
    
    async def demonstrate_resources(self):
        """Demonstrate available resources."""
        print("\n=== Resources Demo ===")
        
        try:
            # Get Hello World server
            hello_world_server = self.mcp_manager.get_server("hello_world_http")
            
            if not hello_world_server:
                print("❌ Hello World server not available")
                return False
            
            # List resources
            resources = await hello_world_server.list_resources()
            print(f"Available resources: {[r['name'] for r in resources]}")
            
            for resource in resources:
                print(f"  Resource: {resource['name']}")
                print(f"    URI: {resource['uri']}")
                print(f"    Description: {resource['description']}")
                print(f"    MIME Type: {resource['mimeType']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error demonstrating resources: {e}")
            return False
    
    async def run_example(self):
        """Run the complete example."""
        print("🚀 Hello World MCP Server Example")
        print("=" * 50)
        
        try:
            # Setup
            await self.setup()
            
            # Run demonstrations
            results = {}
            
            results["hello_world_tool"] = await self.demonstrate_hello_world_tool()
            results["echo_tool"] = await self.demonstrate_echo_tool()
            results["ping_tool"] = await self.demonstrate_ping_tool()
            results["server_info_tool"] = await self.demonstrate_server_info_tool()
            results["all_tools"] = await self.demonstrate_all_tools()
            results["resources"] = await self.demonstrate_resources()
            
            # Print summary
            self.print_summary(results)
            
        except Exception as e:
            print(f"❌ Example error: {e}")
            results = {"general_error": False}
        
        finally:
            # Cleanup
            if self.mcp_manager:
                await self.mcp_manager.stop()
    
    def print_summary(self, results):
        """Print example summary."""
        print("\n" + "="*50)
        print("EXAMPLE SUMMARY")
        print("="*50)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for demo_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{demo_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} demonstrations successful")
        
        if passed == total:
            print("🎉 All demonstrations successful! The Hello World MCP Server is working perfectly.")
        else:
            print("⚠️  Some demonstrations failed. Please check the server configuration.")


async def main():
    """Main function."""
    example = HelloWorldMCPExample()
    await example.run_example()


if __name__ == "__main__":
    asyncio.run(main()) 