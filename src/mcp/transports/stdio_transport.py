"""STDIO transport implementation for MCP servers."""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional
from subprocess import Popen, PIPE

from .base_transport import BaseTransport
from utils.logger import LoggerMixin


class STDIOTransport(BaseTransport, LoggerMixin):
    """STDIO transport for MCP servers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize STDIO transport."""
        super().__init__(config)
        self.command = config.get("command", "")
        self.args = config.get("args", [])
        self.working_dir = config.get("working_dir", None)
        self.env = config.get("env", None)
        self.process: Optional[Popen] = None
        self.request_id = 0
        
    async def connect(self) -> bool:
        """Connect to the MCP server via STDIO."""
        try:
            self.logger.debug(f"Connecting to MCP server with config: {self.config}")
            
            if not self.command:
                self.logger.error("No command specified for STDIO transport")
                return False
            
            # Auto-detect Python executable if command is "python"
            if self.command == "python":
                self.logger.debug("Auto-detecting Python executable")
                self.command = self._get_python_executable()
                self.logger.info(f"Using Python executable: {self.command}")
            
            # Start the process
            cmd = [self.command] + self.args
            
            # Ensure environment is a proper dictionary
            env_dict = None
            if self.env:
                if isinstance(self.env, dict):
                    env_dict = self.env
                else:
                    self.logger.warning(f"Environment is not a dict: {type(self.env)}")
            
            self.logger.debug(f"Starting process: {cmd}")
            self.logger.debug(f"Working directory: {self.working_dir}")
            self.logger.debug(f"Environment: {env_dict}")
            
            self.process = Popen(
                cmd,
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
                cwd=self.working_dir,
                env=env_dict,
                text=True,
                bufsize=1
            )
            
            self.is_connected = True
            self.logger.info(f"Connected to MCP server via STDIO: {self.command}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server via STDIO: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from the MCP server."""
        try:
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except:
                    self.process.kill()
                self.process = None
            
            self.is_connected = False
            self.logger.info("Disconnected from MCP server via STDIO")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from MCP server: {e}")
            return False
    
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to the MCP server via STDIO."""
        if not self.is_connected or not self.process:
            raise ConnectionError("STDIO transport not connected")
        
        try:
            # Convert message to JSON string
            message_str = json.dumps(message) + "\n"
            
            # Send message
            self.process.stdin.write(message_str)
            self.process.stdin.flush()
            
            # Read response
            response_line = self.process.stdout.readline()
            if not response_line:
                raise ConnectionError("No response from MCP server")
            
            # Parse response
            response = self.parse_message(response_line.strip())
            
            # Validate response
            if not self.validate_response(response):
                error_msg = self.get_error_from_response(response)
                if error_msg:
                    raise Exception(error_msg)
                else:
                    raise Exception("Invalid response from MCP server")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error sending message via STDIO: {e}")
            raise
    
    async def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive a message from the MCP server via STDIO."""
        if not self.is_connected or not self.process:
            return None
        
        try:
            # Read a line from stdout
            line = self.process.stdout.readline()
            if not line:
                return None
            
            # Parse the message
            message = self.parse_message(line.strip())
            return message
            
        except Exception as e:
            self.logger.error(f"Error receiving message via STDIO: {e}")
            return None
    
    def get_next_request_id(self) -> str:
        """Get the next request ID."""
        self.request_id += 1
        return str(self.request_id)
    
    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the MCP server."""
        request_id = self.get_next_request_id()
        message = self.format_message(method, params, request_id)
        return await self.send_message(message)
    
    def is_process_alive(self) -> bool:
        """Check if the process is still alive."""
        if not self.process:
            return False
        
        return self.process.poll() is None
    
    def _get_python_executable(self) -> str:
        """Get the Python executable path, preferring virtual environment."""
        import os
        
        try:
            # Check for virtual environment
            venv_paths = [
                ".venv/Scripts/python.exe",  # Windows
                ".venv/bin/python",          # Linux/Mac
                "venv/Scripts/python.exe",   # Windows (alternative)
                "venv/bin/python",           # Linux/Mac (alternative)
            ]
            
            for venv_path in venv_paths:
                if os.path.exists(venv_path):
                    self.logger.debug(f"Found Python executable: {venv_path}")
                    return venv_path
            
            # Fallback to system Python
            self.logger.debug("Using system Python")
            return "python"
        except Exception as e:
            self.logger.error(f"Error getting Python executable: {e}")
            return "python" 