#!/usr/bin/env python3
"""
Hello World HTTP MCP Server

A simple HTTP-based MCP server for testing connectivity and configuration.
This server provides basic "Hello World" functionality and health checks.

Usage: python mcp_servers/hello_world_http_server.py
"""

import json
import sys
import os
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse
    import uvicorn
    from pydantic import BaseModel
except ImportError as e:
    print(f"Error: Required dependencies not found. Please install: pip install fastapi uvicorn")
    print(f"Missing: {e}")
    sys.exit(1)


class MCPRequest(BaseModel):
    """MCP request model."""
    jsonrpc: str
    id: str
    method: str
    params: Dict[str, Any] = {}


class MCPResponse(BaseModel):
    """MCP response model."""
    jsonrpc: str = "2.0"
    id: str
    result: Dict[str, Any] = None
    error: Dict[str, Any] = None


class HelloWorldHTTPMCPServer:
    """Simple HTTP MCP server for Hello World testing."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8081):
        """Initialize the Hello World HTTP MCP server."""
        self.host = host
        self.port = port
        self.app = FastAPI(title="Hello World MCP Server", version="1.0.0")
        self.setup_routes()
        self.request_count = 0
        
    def setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint for basic connectivity test."""
            return {
                "message": "Hello World MCP Server is running!",
                "timestamp": datetime.now().isoformat(),
                "server_info": {
                    "name": "hello-world-mcp-server",
                    "version": "1.0.0",
                    "protocol": "HTTP"
                }
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime": "running",
                "requests_processed": self.request_count
            }
        
        @self.app.post("/mcp")
        async def handle_mcp_request(request: MCPRequest):
            """Handle MCP protocol requests."""
            self.request_count += 1
            
            try:
                if request.method == "initialize":
                    return await self.handle_initialize(request.params, request.id)
                elif request.method == "tools/list":
                    return await self.handle_tools_list(request.params, request.id)
                elif request.method == "tools/call":
                    return await self.handle_tools_call(request.params, request.id)
                elif request.method == "resources/list":
                    return await self.handle_resources_list(request.params, request.id)
                else:
                    return self.create_error_response(
                        request.id, 
                        -32601, 
                        f"Method not found: {request.method}"
                    )
                    
            except Exception as e:
                return self.create_error_response(
                    request.id, 
                    -32603, 
                    f"Internal error: {str(e)}"
                )
    
    def create_success_response(self, result: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Create a successful MCP response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
    
    def create_error_response(self, request_id: str, code: int, message: str) -> Dict[str, Any]:
        """Create an error MCP response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
    
    async def handle_initialize(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Handle initialize request."""
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": True
                },
                "resources": {
                    "listChanged": True
                }
            },
            "serverInfo": {
                "name": "hello-world-mcp-server",
                "version": "1.0.0"
            }
        }
        return self.create_success_response(result, request_id)
    
    async def handle_tools_list(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools = [
            {
                "name": "hello_world",
                "description": "Returns a simple Hello World message",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name to greet (optional)",
                            "default": "World"
                        },
                        "language": {
                            "type": "string",
                            "description": "Language for greeting (optional)",
                            "enum": ["en", "es", "fr", "de"],
                            "default": "en"
                        }
                    }
                }
            },
            {
                "name": "echo",
                "description": "Echo back the input message",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to echo back"
                        }
                    },
                    "required": ["message"]
                }
            },
            {
                "name": "get_server_info",
                "description": "Get server information and status",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "ping",
                "description": "Simple ping test for connectivity",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "string",
                            "description": "Optional data to include in ping response"
                        }
                    }
                }
            }
        ]
        
        result = {"tools": tools}
        return self.create_success_response(result, request_id)
    
    async def handle_tools_call(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "hello_world":
            result = await self.hello_world(arguments)
        elif tool_name == "echo":
            result = await self.echo(arguments)
        elif tool_name == "get_server_info":
            result = await self.get_server_info(arguments)
        elif tool_name == "ping":
            result = await self.ping(arguments)
        else:
            return self.create_error_response(
                request_id, 
                -32601, 
                f"Tool not found: {tool_name}"
            )
        
        return self.create_success_response({"content": result}, request_id)
    
    async def handle_resources_list(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Handle resources/list request."""
        resources = [
            {
                "uri": "hello-world://server/info",
                "name": "Server Information",
                "description": "Basic server information and status",
                "mimeType": "application/json"
            }
        ]
        
        result = {"resources": resources}
        return self.create_success_response(result, request_id)
    
    async def hello_world(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Hello World tool implementation."""
        name = args.get("name", "World")
        language = args.get("language", "en")
        
        greetings = {
            "en": f"Hello, {name}!",
            "es": f"¡Hola, {name}!",
            "fr": f"Bonjour, {name}!",
            "de": f"Hallo, {name}!"
        }
        
        greeting = greetings.get(language, greetings["en"])
        
        return [
            {
                "type": "text",
                "text": greeting
            },
            {
                "type": "text",
                "text": f"Server timestamp: {datetime.now().isoformat()}"
            }
        ]
    
    async def echo(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Echo tool implementation."""
        message = args.get("message", "")
        
        return [
            {
                "type": "text",
                "text": f"Echo: {message}"
            }
        ]
    
    async def get_server_info(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get server info tool implementation."""
        info = {
            "server_name": "Hello World MCP Server",
            "version": "1.0.0",
            "protocol": "HTTP",
            "host": self.host,
            "port": self.port,
            "timestamp": datetime.now().isoformat(),
            "requests_processed": self.request_count,
            "status": "running"
        }
        
        return [
            {
                "type": "text",
                "text": f"Server Information:\n{json.dumps(info, indent=2)}"
            }
        ]
    
    async def ping(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Ping tool implementation."""
        data = args.get("data", "")
        response = f"Pong! {datetime.now().isoformat()}"
        
        if data:
            response += f" Data: {data}"
        
        return [
            {
                "type": "text",
                "text": response
            }
        ]
    
    def run(self):
        """Run the HTTP server."""
        print(f"Starting Hello World MCP Server on {self.host}:{self.port}")
        print(f"Server URL: http://{self.host}:{self.port}")
        print(f"Health check: http://{self.host}:{self.port}/health")
        print(f"MCP endpoint: http://{self.host}:{self.port}/mcp")
        print("Press Ctrl+C to stop the server")
        
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hello World HTTP MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8081, help="Port to bind to")
    
    args = parser.parse_args()
    
    server = HelloWorldHTTPMCPServer(host=args.host, port=args.port)
    server.run()


if __name__ == "__main__":
    main() 