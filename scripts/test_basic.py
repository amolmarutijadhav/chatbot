#!/usr/bin/env python3
"""Simple test script to verify basic functionality."""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config_manager import ConfigurationManager
from utils.logger import setup_logging
from core.session_manager import SessionManager
from core.context_manager import ContextManager


async def test_basic_functionality():
    """Test basic functionality of the chatbot system."""
    print("Testing Intelligent MCP Chatbot - Basic Functionality")
    print("=" * 60)
    
    try:
        # Initialize configuration
        print("1. Initializing configuration...")
        config_manager = ConfigurationManager()
        print(f"   ✓ Configuration loaded successfully")
        
        # Setup logging
        print("2. Setting up logging...")
        setup_logging(level="INFO", console_output=True)
        print(f"   ✓ Logging configured successfully")
        
        # Create session manager
        print("3. Creating session manager...")
        session_config = config_manager.get_session_config()
        session_manager = SessionManager(session_config)
        await session_manager.start()
        print(f"   ✓ Session manager started successfully")
        
        # Create context manager
        print("4. Creating context manager...")
        context_manager = ContextManager(session_manager)
        print(f"   ✓ Context manager created successfully")
        
        # Test session creation
        print("5. Testing session creation...")
        session = await session_manager.create_session("test_user", {"source": "test_script"})
        print(f"   ✓ Session created: {session.session_id}")
        
        # Test context building
        print("6. Testing context building...")
        context = await context_manager.build_context(
            session.session_id,
            "Hello, this is a test message",
            "chat"
        )
        print(f"   ✓ Context built: {context.correlation_id}")
        
        # Test context analysis
        print("7. Testing context analysis...")
        keywords = context_manager.extract_keywords(context)
        sentiment = context_manager.get_context_sentiment(context)
        should_use_mcp = context_manager.should_use_mcp(context)
        
        print(f"   ✓ Keywords extracted: {keywords[:5]}...")
        print(f"   ✓ Sentiment: {sentiment}")
        print(f"   ✓ Should use MCP: {should_use_mcp}")
        
        # Test MCP-related context
        print("8. Testing MCP-related context...")
        mcp_context = await context_manager.build_context(
            session.session_id,
            "Please read the file config.yaml",
            "chat"
        )
        
        should_use_mcp = context_manager.should_use_mcp(mcp_context)
        suggested_servers = context_manager.get_suggested_mcp_servers(mcp_context)
        
        print(f"   ✓ Should use MCP: {should_use_mcp}")
        print(f"   ✓ Suggested servers: {suggested_servers}")
        
        # Test session statistics
        print("9. Testing session statistics...")
        stats = session_manager.get_session_stats()
        print(f"   ✓ Session stats: {stats}")
        
        # Test session updates
        print("10. Testing session updates...")
        await session_manager.add_mcp_server_to_session(session.session_id, "file_system")
        updated_session = await session_manager.get_session(session.session_id)
        print(f"   ✓ MCP servers: {updated_session.mcp_servers}")
        
        # Clean up
        print("11. Cleaning up...")
        await session_manager.stop()
        print(f"   ✓ Session manager stopped successfully")
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed successfully!")
        print("The Intelligent MCP Chatbot system is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_basic_functionality())
    sys.exit(0 if success else 1) 