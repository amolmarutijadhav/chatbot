"""Main entry point for the Intelligent MCP Chatbot."""

import asyncio
import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from utils.config_manager import ConfigurationManager
from utils.logger import setup_logging
from utils.event_bus import get_event_bus
from core.chatbot_engine import ChatbotEngine


async def main():
    """Main entry point for the chatbot system."""
    try:
        # Initialize configuration
        config_manager = ConfigurationManager()
        
        # Setup logging
        logging_config = config_manager.get_logging_config()
        setup_logging(
            level=logging_config.get("level", "INFO"),
            log_file=logging_config.get("file"),
            max_file_size=logging_config.get("max_file_size", "10MB"),
            backup_count=logging_config.get("backup_count", 5),
            console_output=logging_config.get("console_output", True),
            structured=logging_config.get("structured", {}).get("enabled", True)
        )
        
        # Validate configuration
        if not config_manager.validate():
            print("Configuration validation failed. Please check your configuration files.")
            sys.exit(1)
        
        # Get event bus
        event_bus = get_event_bus()
        
        # Create and start chatbot engine
        chatbot_engine = ChatbotEngine(config_manager)
        await chatbot_engine.start()
        
        print("Intelligent MCP Chatbot started successfully!")
        print(f"Configuration loaded: {config_manager.get('chatbot.name')} v{config_manager.get('chatbot.version')}")
        
        # Keep the application running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
        
        # Stop the chatbot engine
        await chatbot_engine.stop()
        
    except Exception as e:
        print(f"Error starting chatbot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 