"""Basic usage example for the Intelligent MCP Chatbot."""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config_manager import ConfigurationManager
from utils.logger import setup_logging
from core.session_manager import SessionManager
from core.context_manager import ContextManager
from core.models import ChatRequest, Response


async def basic_example():
    """Basic example demonstrating core functionality."""
    
    # Initialize configuration
    config_manager = ConfigurationManager()
    
    # Setup logging
    setup_logging(level="INFO", console_output=True)
    
    # Create session manager
    session_config = config_manager.get_session_config()
    session_manager = SessionManager(session_config)
    await session_manager.start()
    
    # Create context manager
    context_manager = ContextManager(session_manager)
    
    try:
        # Create a session
        print("Creating session...")
        session = await session_manager.create_session("user123", {"source": "example"})
        print(f"Session created: {session.session_id}")
        
        # Process a simple message
        print("\nProcessing message...")
        context = await context_manager.build_context(
            session.session_id,
            "Hello, how are you?",
            "chat"
        )
        
        print(f"Context built: {context.correlation_id}")
        print(f"Message: {context.message}")
        print(f"User ID: {context.user_id}")
        
        # Get context summary
        summary = await context_manager.get_context_summary(context)
        print(f"\nContext summary: {summary}")
        
        # Extract keywords
        keywords = context_manager.extract_keywords(context)
        print(f"Keywords: {keywords}")
        
        # Get sentiment
        sentiment = context_manager.get_context_sentiment(context)
        print(f"Sentiment: {sentiment}")
        
        # Check if MCP should be used
        should_use_mcp = context_manager.should_use_mcp(context)
        print(f"Should use MCP: {should_use_mcp}")
        
        # Process a message that should use MCP
        print("\nProcessing MCP-related message...")
        mcp_context = await context_manager.build_context(
            session.session_id,
            "Please read the file config.yaml",
            "chat"
        )
        
        should_use_mcp = context_manager.should_use_mcp(mcp_context)
        print(f"Should use MCP: {should_use_mcp}")
        
        suggested_servers = context_manager.get_suggested_mcp_servers(mcp_context)
        print(f"Suggested MCP servers: {suggested_servers}")
        
        # Get session statistics
        stats = session_manager.get_session_stats()
        print(f"\nSession statistics: {stats}")
        
        # Update session with MCP server
        print("\nAdding MCP server to session...")
        await session_manager.add_mcp_server_to_session(session.session_id, "file_system")
        
        # Get updated session
        updated_session = await session_manager.get_session(session.session_id)
        print(f"Session MCP servers: {updated_session.mcp_servers}")
        
    finally:
        # Clean up
        await session_manager.stop()
        print("\nExample completed!")


async def session_management_example():
    """Example demonstrating session management features."""
    
    config_manager = ConfigurationManager()
    session_config = config_manager.get_session_config()
    session_manager = SessionManager(session_config)
    await session_manager.start()
    
    try:
        # Create multiple sessions for the same user
        print("Creating multiple sessions...")
        session1 = await session_manager.create_session("user456")
        session2 = await session_manager.create_session("user456")
        session3 = await session_manager.create_session("user456")
        
        print(f"Created sessions: {session1.session_id}, {session2.session_id}, {session3.session_id}")
        
        # Get all sessions for user
        user_sessions = await session_manager.get_user_sessions("user456")
        print(f"User sessions count: {len(user_sessions)}")
        
        # Update session
        await session_manager.update_session(session1.session_id, {
            "metadata": {"last_action": "file_operation"}
        })
        
        # Get session statistics
        stats = session_manager.get_session_stats()
        print(f"Session stats: {stats}")
        
        # Close a session
        await session_manager.close_session(session2.session_id)
        
        # Verify session is closed
        closed_session = await session_manager.get_session(session2.session_id)
        print(f"Session 2 is active: {closed_session is not None}")
        
    finally:
        await session_manager.stop()


if __name__ == "__main__":
    print("Intelligent MCP Chatbot - Basic Usage Example")
    print("=" * 50)
    
    # Run basic example
    asyncio.run(basic_example())
    
    print("\n" + "=" * 50)
    
    # Run session management example
    asyncio.run(session_management_example()) 