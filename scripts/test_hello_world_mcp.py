#!/usr/bin/env python3
"""
Test script for Hello World HTTP MCP Server

This script tests the connectivity and functionality of the Hello World HTTP MCP server.
It can be used to verify that the server is working correctly before integrating with the chatbot.

Usage: python scripts/test_hello_world_mcp.py
"""

import json
import sys
import asyncio
import aiohttp
import uuid
from typing import Dict, Any, Optional
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class HelloWorldMCPTester:
    """Test client for Hello World HTTP MCP Server."""
    
    def __init__(self, base_url: str = "http://localhost:8081"):
        """Initialize the test client."""
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_id = 0
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def get_next_request_id(self) -> str:
        """Get the next request ID."""
        self.request_id += 1
        return str(self.request_id)
    
    async def send_mcp_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send an MCP request to the server."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        request_data = {
            "jsonrpc": "2.0",
            "id": self.get_next_request_id(),
            "method": method,
            "params": params or {}
        }
        
        print(f"Sending request: {method}")
        print(f"Request data: {json.dumps(request_data, indent=2)}")
        
        async with self.session.post(f"{self.base_url}/mcp", json=request_data) as response:
            if response.status == 200:
                data = await response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                return data
            else:
                error_text = await response.text()
                print(f"HTTP Error {response.status}: {error_text}")
                raise Exception(f"HTTP error {response.status}: {error_text}")
    
    async def test_health_check(self) -> bool:
        """Test the health check endpoint."""
        print("\n=== Testing Health Check ===")
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"Health check response: {json.dumps(data, indent=2)}")
                    return True
                else:
                    print(f"Health check failed with status {response.status}")
                    return False
        except Exception as e:
            print(f"Health check error: {e}")
            return False
    
    async def test_root_endpoint(self) -> bool:
        """Test the root endpoint."""
        print("\n=== Testing Root Endpoint ===")
        try:
            async with self.session.get(self.base_url) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"Root endpoint response: {json.dumps(data, indent=2)}")
                    return True
                else:
                    print(f"Root endpoint failed with status {response.status}")
                    return False
        except Exception as e:
            print(f"Root endpoint error: {e}")
            return False
    
    async def test_initialize(self) -> bool:
        """Test the initialize method."""
        print("\n=== Testing Initialize ===")
        try:
            result = await self.send_mcp_request("initialize")
            if "result" in result:
                print("✅ Initialize successful")
                return True
            else:
                print("❌ Initialize failed")
                return False
        except Exception as e:
            print(f"❌ Initialize error: {e}")
            return False
    
    async def test_tools_list(self) -> bool:
        """Test the tools/list method."""
        print("\n=== Testing Tools List ===")
        try:
            result = await self.send_mcp_request("tools/list")
            if "result" in result and "tools" in result["result"]:
                tools = result["result"]["tools"]
                print(f"✅ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"  - {tool['name']}: {tool['description']}")
                return True
            else:
                print("❌ Tools list failed")
                return False
        except Exception as e:
            print(f"❌ Tools list error: {e}")
            return False
    
    async def test_hello_world_tool(self) -> bool:
        """Test the hello_world tool."""
        print("\n=== Testing Hello World Tool ===")
        try:
            result = await self.send_mcp_request("tools/call", {
                "name": "hello_world",
                "arguments": {
                    "name": "QA Tester",
                    "language": "en"
                }
            })
            if "result" in result and "content" in result["result"]:
                print("✅ Hello World tool successful")
                return True
            else:
                print("❌ Hello World tool failed")
                return False
        except Exception as e:
            print(f"❌ Hello World tool error: {e}")
            return False
    
    async def test_echo_tool(self) -> bool:
        """Test the echo tool."""
        print("\n=== Testing Echo Tool ===")
        try:
            test_message = "Hello from QA tester!"
            result = await self.send_mcp_request("tools/call", {
                "name": "echo",
                "arguments": {
                    "message": test_message
                }
            })
            if "result" in result and "content" in result["result"]:
                print("✅ Echo tool successful")
                return True
            else:
                print("❌ Echo tool failed")
                return False
        except Exception as e:
            print(f"❌ Echo tool error: {e}")
            return False
    
    async def test_ping_tool(self) -> bool:
        """Test the ping tool."""
        print("\n=== Testing Ping Tool ===")
        try:
            result = await self.send_mcp_request("tools/call", {
                "name": "ping",
                "arguments": {
                    "data": "test_data"
                }
            })
            if "result" in result and "content" in result["result"]:
                print("✅ Ping tool successful")
                return True
            else:
                print("❌ Ping tool failed")
                return False
        except Exception as e:
            print(f"❌ Ping tool error: {e}")
            return False
    
    async def test_server_info_tool(self) -> bool:
        """Test the get_server_info tool."""
        print("\n=== Testing Server Info Tool ===")
        try:
            result = await self.send_mcp_request("tools/call", {
                "name": "get_server_info",
                "arguments": {}
            })
            if "result" in result and "content" in result["result"]:
                print("✅ Server info tool successful")
                return True
            else:
                print("❌ Server info tool failed")
                return False
        except Exception as e:
            print(f"❌ Server info tool error: {e}")
            return False
    
    async def test_resources_list(self) -> bool:
        """Test the resources/list method."""
        print("\n=== Testing Resources List ===")
        try:
            result = await self.send_mcp_request("resources/list")
            if "result" in result and "resources" in result["result"]:
                resources = result["result"]["resources"]
                print(f"✅ Found {len(resources)} resources:")
                for resource in resources:
                    print(f"  - {resource['name']}: {resource['description']}")
                return True
            else:
                print("❌ Resources list failed")
                return False
        except Exception as e:
            print(f"❌ Resources list error: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results."""
        print("🚀 Starting Hello World MCP Server Tests")
        print(f"Target URL: {self.base_url}")
        
        results = {}
        
        # Test basic connectivity
        results["health_check"] = await self.test_health_check()
        results["root_endpoint"] = await self.test_root_endpoint()
        
        # Test MCP protocol
        results["initialize"] = await self.test_initialize()
        results["tools_list"] = await self.test_tools_list()
        results["resources_list"] = await self.test_resources_list()
        
        # Test individual tools
        results["hello_world_tool"] = await self.test_hello_world_tool()
        results["echo_tool"] = await self.test_echo_tool()
        results["ping_tool"] = await self.test_ping_tool()
        results["server_info_tool"] = await self.test_server_info_tool()
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """Print test summary."""
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! The Hello World MCP Server is working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the server configuration.")


async def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Hello World HTTP MCP Server")
    parser.add_argument("--url", default="http://localhost:8081", 
                       help="Base URL of the MCP server")
    
    args = parser.parse_args()
    
    async with HelloWorldMCPTester(args.url) as tester:
        results = await tester.run_all_tests()
        tester.print_summary(results)
        
        # Exit with appropriate code
        if all(results.values()):
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 