#!/usr/bin/env python3
"""
Simple MCP File System Server

This server provides basic file system operations:
- List files in a directory
- Read file contents
- Get file information
- Search files by pattern

Usage: python mcp_servers/filesystem_server.py
"""

import json
import sys
import os
import glob
from pathlib import Path
from typing import Dict, Any, List
import uuid
from datetime import datetime


class FileSystemMCPServer:
    """Simple MCP server for file system operations."""
    
    def __init__(self, root_path: str = "."):
        """Initialize the file system server."""
        self.root_path = Path(root_path).resolve()
        self.request_id = 0
        
    def send_response(self, result: Any = None, error: str = None, id: str = None):
        """Send a response to the client."""
        response = {
            "jsonrpc": "2.0",
            "id": id
        }
        
        if error:
            response["error"] = {
                "code": -1,
                "message": error
            }
        else:
            response["result"] = result
        
        # Send response to stdout
        print(json.dumps(response), flush=True)
    
    def handle_initialize(self, params: Dict[str, Any], request_id: str):
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
                "name": "filesystem-server",
                "version": "1.0.0"
            }
        }
        self.send_response(result=result, id=request_id)
    
    def handle_tools_list(self, params: Dict[str, Any], request_id: str):
        """Handle tools/list request."""
        tools = [
            {
                "name": "list_files",
                "description": "List files in a directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path to list (relative to root)"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "File pattern to match (e.g., *.txt)"
                        }
                    }
                }
            },
            {
                "name": "read_file",
                "description": "Read contents of a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path to read (relative to root)"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding (default: utf-8)"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "file_info",
                "description": "Get information about a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path to get info for (relative to root)"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "search_files",
                "description": "Search for files by pattern",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Search pattern (e.g., *.py)"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Search recursively (default: false)"
                        }
                    },
                    "required": ["pattern"]
                }
            }
        ]
        
        result = {"tools": tools}
        self.send_response(result=result, id=request_id)
    
    def handle_tools_call(self, params: Dict[str, Any], request_id: str):
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "list_files":
                result = self.list_files(arguments)
            elif tool_name == "read_file":
                result = self.read_file(arguments)
            elif tool_name == "file_info":
                result = self.file_info(arguments)
            elif tool_name == "search_files":
                result = self.search_files(arguments)
            else:
                raise Exception(f"Unknown tool: {tool_name}")
            
            self.send_response(result=result, id=request_id)
            
        except Exception as e:
            self.send_response(error=str(e), id=request_id)
    
    def list_files(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List files in a directory."""
        path = args.get("path", ".")
        pattern = args.get("pattern")
        
        target_path = self.root_path / path
        
        if not target_path.exists():
            raise Exception(f"Path does not exist: {path}")
        
        if not target_path.is_dir():
            raise Exception(f"Path is not a directory: {path}")
        
        files = []
        if pattern:
            # Use glob pattern
            for file_path in target_path.glob(pattern):
                files.append({
                    "name": file_path.name,
                    "path": str(file_path.relative_to(self.root_path)),
                    "type": "file" if file_path.is_file() else "directory",
                    "size": file_path.stat().st_size if file_path.is_file() else None
                })
        else:
            # List all files
            for file_path in target_path.iterdir():
                files.append({
                    "name": file_path.name,
                    "path": str(file_path.relative_to(self.root_path)),
                    "type": "file" if file_path.is_file() else "directory",
                    "size": file_path.stat().st_size if file_path.is_file() else None
                })
        
        return {
            "files": files,
            "count": len(files),
            "path": str(target_path.relative_to(self.root_path))
        }
    
    def read_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Read contents of a file."""
        path = args["path"]
        encoding = args.get("encoding", "utf-8")
        
        target_path = self.root_path / path
        
        if not target_path.exists():
            raise Exception(f"File does not exist: {path}")
        
        if not target_path.is_file():
            raise Exception(f"Path is not a file: {path}")
        
        try:
            with open(target_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return {
                "content": content,
                "path": str(target_path.relative_to(self.root_path)),
                "size": len(content),
                "encoding": encoding
            }
        except UnicodeDecodeError:
            raise Exception(f"Could not decode file with encoding {encoding}")
    
    def file_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about a file."""
        path = args["path"]
        
        target_path = self.root_path / path
        
        if not target_path.exists():
            raise Exception(f"File does not exist: {path}")
        
        stat = target_path.stat()
        
        return {
            "name": target_path.name,
            "path": str(target_path.relative_to(self.root_path)),
            "type": "file" if target_path.is_file() else "directory",
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "permissions": oct(stat.st_mode)[-3:]
        }
    
    def search_files(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search for files by pattern."""
        pattern = args["pattern"]
        recursive = args.get("recursive", True)  # Default to recursive search
        
        files = []
        
        # Handle different search patterns
        if pattern.startswith("*") and pattern.endswith("*"):
            # Pattern like "*test*" - search for files containing the term
            search_term = pattern[1:-1]  # Remove the *s
            if recursive:
                search_paths = self.root_path.rglob("*")
            else:
                search_paths = self.root_path.glob("*")
                
            for file_path in search_paths:
                if file_path.is_file() and search_term.lower() in file_path.name.lower():
                    files.append({
                        "name": file_path.name,
                        "path": str(file_path.relative_to(self.root_path)),
                        "size": file_path.stat().st_size
                    })
        else:
            # Direct glob pattern
            if recursive:
                search_pattern = f"**/{pattern}"
            else:
                search_pattern = pattern
            
            for file_path in self.root_path.glob(search_pattern):
                if file_path.is_file():
                    files.append({
                        "name": file_path.name,
                        "path": str(file_path.relative_to(self.root_path)),
                        "size": file_path.stat().st_size
                    })
        
        return {
            "files": files,
            "count": len(files),
            "pattern": pattern,
            "recursive": recursive
        }
    
    def run(self):
        """Run the MCP server."""
        print("File System MCP Server started", file=sys.stderr)
        print(f"Root path: {self.root_path}", file=sys.stderr)
        
        try:
            while True:
                # Read request from stdin
                line = sys.stdin.readline()
                if not line:
                    break
                
                try:
                    request = json.loads(line.strip())
                    
                    # Extract request details
                    method = request.get("method")
                    params = request.get("params", {})
                    request_id = request.get("id")
                    
                    # Handle different methods
                    if method == "initialize":
                        self.handle_initialize(params, request_id)
                    elif method == "tools/list":
                        self.handle_tools_list(params, request_id)
                    elif method == "tools/call":
                        self.handle_tools_call(params, request_id)
                    else:
                        self.send_response(
                            error=f"Unknown method: {method}",
                            id=request_id
                        )
                        
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON: {e}", file=sys.stderr)
                    continue
                except Exception as e:
                    print(f"Error processing request: {e}", file=sys.stderr)
                    continue
                    
        except KeyboardInterrupt:
            print("Server stopped by user", file=sys.stderr)
        except Exception as e:
            print(f"Server error: {e}", file=sys.stderr)


if __name__ == "__main__":
    # Get root path from environment or use current directory
    root_path = os.getenv("MCP_FS_ROOT", ".")
    
    server = FileSystemMCPServer(root_path)
    server.run() 