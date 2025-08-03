#!/usr/bin/env python3
"""
Startup script for Hello World HTTP MCP Server

This script provides an easy way to start the Hello World HTTP MCP server
with proper environment setup and error handling.

Usage: python scripts/start_hello_world_server.py
"""

import sys
import os
import subprocess
import signal
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        print("✅ Required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install required dependencies:")
        print("pip install fastapi uvicorn")
        return False


def check_virtual_environment():
    """Check if virtual environment is activated."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment is activated")
        return True
    else:
        print("⚠️  Virtual environment not detected")
        print("Consider activating the virtual environment:")
        print("source .venv/bin/activate  # Linux/Mac")
        print(".venv\\Scripts\\activate    # Windows")
        return True  # Don't fail, just warn


def start_server(host="0.0.0.0", port=8081):
    """Start the Hello World HTTP MCP server."""
    print(f"🚀 Starting Hello World HTTP MCP Server...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Server URL: http://{host}:{port}")
    print(f"Health check: http://{host}:{port}/health")
    print(f"MCP endpoint: http://{host}:{port}/mcp")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Build the command
    server_script = project_root / "mcp_servers" / "hello_world_http_server.py"
    cmd = [
        sys.executable,
        str(server_script),
        "--host", host,
        "--port", str(port)
    ]
    
    try:
        # Start the server process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Monitor the process
        while True:
            output = process.stdout.readline()
            if output:
                print(output.rstrip())
            
            # Check if process is still running
            if process.poll() is not None:
                print(f"❌ Server process exited with code {process.returncode}")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
                print("✅ Server stopped gracefully")
            except subprocess.TimeoutExpired:
                print("⚠️  Server didn't stop gracefully, forcing termination")
                process.kill()
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False
    
    return True


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start Hello World HTTP MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8081, help="Port to bind to")
    parser.add_argument("--check-only", action="store_true", 
                       help="Only check dependencies and environment")
    
    args = parser.parse_args()
    
    print("🔧 Hello World HTTP MCP Server Startup")
    print("=" * 50)
    
    # Check environment
    if not check_dependencies():
        sys.exit(1)
    
    check_virtual_environment()
    
    if args.check_only:
        print("✅ Environment check complete")
        return
    
    # Start the server
    success = start_server(args.host, args.port)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main() 