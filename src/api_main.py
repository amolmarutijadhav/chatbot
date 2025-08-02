"""Main entry point for running the Intelligent MCP Chatbot API server."""

import asyncio
import signal
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from utils.config_manager import ConfigurationManager
from utils.logger import setup_logging, get_logger
from api.server import run_server

logger = get_logger(__name__)


def main():
    """Main function to run the API server."""
    try:
        # Load configuration
        config_manager = ConfigurationManager()
        config = config_manager.get_all_config()
        
        # Setup logging
        logging_config = config.get("logging", {})
        # Remove unsupported parameters
        supported_params = {
            'level', 'log_file', 'max_file_size', 'backup_count', 
            'console_output', 'structured', 'include_timestamp', 'include_correlation_id'
        }
        filtered_config = {k: v for k, v in logging_config.items() if k in supported_params}
        setup_logging(**filtered_config)
        
        # Validate configuration
        if not config_manager.validate_configuration():
            logger.error("Invalid configuration")
            sys.exit(1)
        
        # Get API configuration
        api_config = config.get("api", {})
        host = api_config.get("host", "0.0.0.0")
        port = api_config.get("port", 8000)
        
        logger.info(f"Starting Intelligent MCP Chatbot API server on {host}:{port}")
        logger.info(f"API Documentation: http://{host}:{port}/docs")
        logger.info(f"ReDoc Documentation: http://{host}:{port}/redoc")
        
        # Run the server
        run_server(config, host=host, port=port)
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 