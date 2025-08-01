"""Main entry point for the Intelligent MCP Chatbot."""

import asyncio
import signal
import sys
from pathlib import Path

from utils.config_manager import ConfigurationManager
from utils.logger import setup_logging, get_logger
from utils.event_bus import get_event_bus
from core.chatbot_engine import ChatbotEngine


class ChatbotApplication:
    """Main chatbot application."""
    
    def __init__(self):
        """Initialize the chatbot application."""
        self.config_manager = ConfigurationManager()
        self.chatbot_engine: ChatbotEngine = None
        self.logger = get_logger(__name__)
        self.event_bus = get_event_bus()
        self.running = False
        
    async def start(self):
        """Start the chatbot application."""
        try:
            self.logger.info("Starting Intelligent MCP Chatbot...")
            
            # Setup logging
            logging_config = self.config_manager.get("logging", {})
            setup_logging(**logging_config)
            
            # Validate configuration
            if not self.config_manager.validate_configuration():
                self.logger.error("Invalid configuration")
                return False
            
            # Create and start chatbot engine
            config = self.config_manager.get_all_config()
            self.chatbot_engine = ChatbotEngine(config)
            await self.chatbot_engine.start()
            
            self.running = True
            self.logger.info("Chatbot application started successfully")
            
            # Setup signal handlers
            self._setup_signal_handlers()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start chatbot application: {e}")
            return False
    
    async def stop(self):
        """Stop the chatbot application."""
        try:
            self.logger.info("Stopping chatbot application...")
            
            if self.chatbot_engine:
                await self.chatbot_engine.stop()
            
            self.running = False
            self.logger.info("Chatbot application stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping chatbot application: {e}")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run_demo(self):
        """Run a demo conversation."""
        if not self.running or not self.chatbot_engine:
            self.logger.error("Chatbot not running")
            return
        
        try:
            self.logger.info("Starting demo conversation...")
            
            # Demo messages
            demo_messages = [
                "Hello! How are you today?",
                "Can you explain what machine learning is?",
                "What's the weather like?",
                "List the files in the current directory",
                "Thank you for your help!"
            ]
            
            user_id = "demo_user"
            
            for i, message in enumerate(demo_messages, 1):
                self.logger.info(f"\n--- Demo Message {i} ---")
                self.logger.info(f"User: {message}")
                
                try:
                    response = await self.chatbot_engine.process_message(
                        user_id=user_id,
                        message=message
                    )
                    
                    self.logger.info(f"Assistant: {response.content}")
                    self.logger.info(f"Status: {response.status}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
                
                # Small delay between messages
                await asyncio.sleep(1)
            
            # Show statistics
            await self._show_statistics()
            
        except Exception as e:
            self.logger.error(f"Error in demo: {e}")
    
    async def _show_statistics(self):
        """Show system statistics."""
        try:
            self.logger.info("\n--- System Statistics ---")
            
            # Session stats
            session_stats = await self.chatbot_engine.get_session_stats()
            self.logger.info(f"Session Stats: {session_stats}")
            
            # LLM stats
            llm_stats = await self.chatbot_engine.get_llm_stats()
            self.logger.info(f"LLM Stats: {llm_stats}")
            
            # MCP stats
            mcp_stats = await self.chatbot_engine.get_mcp_stats()
            self.logger.info(f"MCP Stats: {mcp_stats}")
            
            # Health check
            health = await self.chatbot_engine.health_check()
            self.logger.info(f"Health Check: {health}")
            
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
    
    async def run_interactive(self):
        """Run interactive mode."""
        if not self.running or not self.chatbot_engine:
            self.logger.error("Chatbot not running")
            return
        
        try:
            self.logger.info("Starting interactive mode...")
            self.logger.info("Type 'quit' to exit, 'stats' to see statistics")
            
            user_id = "interactive_user"
            
            while self.running:
                try:
                    # Get user input
                    message = input("\nYou: ").strip()
                    
                    if not message:
                        continue
                    
                    if message.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    if message.lower() == 'stats':
                        await self._show_statistics()
                        continue
                    
                    # Process message
                    response = await self.chatbot_engine.process_message(
                        user_id=user_id,
                        message=message
                    )
                    
                    print(f"\nAssistant: {response.content}")
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.logger.error(f"Error: {e}")
                    print(f"\nError: {e}")
            
        except Exception as e:
            self.logger.error(f"Error in interactive mode: {e}")


async def main():
    """Main function."""
    app = ChatbotApplication()
    
    try:
        # Start the application
        if not await app.start():
            sys.exit(1)
        
        # Check command line arguments
        if len(sys.argv) > 1:
            mode = sys.argv[1].lower()
            
            if mode == "demo":
                await app.run_demo()
            elif mode == "interactive":
                await app.run_interactive()
            else:
                print("Usage: python main.py [demo|interactive]")
                print("  demo: Run a demo conversation")
                print("  interactive: Run in interactive mode")
        else:
            # Default to demo
            await app.run_demo()
    
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
    
    finally:
        # Ensure cleanup
        await app.stop()


if __name__ == "__main__":
    # Run the application
    asyncio.run(main()) 