#!/usr/bin/env python3
"""
Simple MCP Integration Test
Tests MCP functionality using the existing demo mode
"""

import asyncio
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.config_manager import ConfigurationManager
from utils.logger import setup_logging, get_logger
from core.chatbot_engine import ChatbotEngine


class SimpleMCPTester:
    """Simple tester for MCP integration."""
    
    def __init__(self):
        """Initialize the tester."""
        self.logger = get_logger(__name__)
        self.config_manager = ConfigurationManager()
        self.engine = None
        
    async def setup(self):
        """Setup the chatbot engine."""
        try:
            # Load configuration
            config = self.config_manager.get_configuration()
            
            # Create chatbot engine
            self.engine = ChatbotEngine(config)
            await self.engine.start()
            
            self.logger.info("✅ Chatbot engine started successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to setup chatbot engine: {e}")
            return False
    
    async def test_mcp_file_listing(self):
        """Test MCP file listing functionality."""
        try:
            self.logger.info("🧪 Testing MCP File Listing...")
            
            # Create context
            context = {
                "user_id": "test_user",
                "message": "List the files in the current directory",
                "session_id": "test_session",
                "message_type": "chat",
                "metadata": {"test": True, "type": "mcp_file_listing"}
            }
            
            # Process message
            response = await self.engine.process_message(**context)
            
            # Check response
            if response.status == "success":
                metadata = response.metadata or {}
                processing_strategy = metadata.get("processing_strategy", "")
                tool_used = metadata.get("tool_used", "")
                
                if "mcp" in processing_strategy.lower() or tool_used == "list_files":
                    self.logger.info("✅ MCP File Listing: SUCCESS")
                    self.logger.info(f"   Strategy: {processing_strategy}")
                    self.logger.info(f"   Tool: {tool_used}")
                    self.logger.info(f"   Response: {response.content[:100]}...")
                    return True
                else:
                    self.logger.error(f"❌ MCP File Listing: Expected MCP but got {processing_strategy}")
                    return False
            else:
                self.logger.error(f"❌ MCP File Listing: Failed with status {response.status}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ MCP File Listing: Error - {e}")
            return False
    
    async def test_mcp_file_info(self):
        """Test MCP file info functionality."""
        try:
            self.logger.info("🧪 Testing MCP File Info...")
            
            # Create context
            context = {
                "user_id": "test_user",
                "message": "Get information about the README.md file",
                "session_id": "test_session",
                "message_type": "chat",
                "metadata": {"test": True, "type": "mcp_file_info"}
            }
            
            # Process message
            response = await self.engine.process_message(**context)
            
            # Check response
            if response.status == "success":
                metadata = response.metadata or {}
                processing_strategy = metadata.get("processing_strategy", "")
                tool_used = metadata.get("tool_used", "")
                
                if "mcp" in processing_strategy.lower() or tool_used == "file_info":
                    self.logger.info("✅ MCP File Info: SUCCESS")
                    self.logger.info(f"   Strategy: {processing_strategy}")
                    self.logger.info(f"   Tool: {tool_used}")
                    self.logger.info(f"   Response: {response.content[:100]}...")
                    return True
                else:
                    self.logger.error(f"❌ MCP File Info: Expected MCP but got {processing_strategy}")
                    return False
            else:
                self.logger.error(f"❌ MCP File Info: Failed with status {response.status}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ MCP File Info: Error - {e}")
            return False
    
    async def test_mcp_file_search(self):
        """Test MCP file search functionality."""
        try:
            self.logger.info("🧪 Testing MCP File Search...")
            
            # Create context
            context = {
                "user_id": "test_user",
                "message": "Search for files containing 'test' in the name",
                "session_id": "test_session",
                "message_type": "chat",
                "metadata": {"test": True, "type": "mcp_file_search"}
            }
            
            # Process message
            response = await self.engine.process_message(**context)
            
            # Check response
            if response.status == "success":
                metadata = response.metadata or {}
                processing_strategy = metadata.get("processing_strategy", "")
                tool_used = metadata.get("tool_used", "")
                
                if "mcp" in processing_strategy.lower() or tool_used == "search_files":
                    self.logger.info("✅ MCP File Search: SUCCESS")
                    self.logger.info(f"   Strategy: {processing_strategy}")
                    self.logger.info(f"   Tool: {tool_used}")
                    self.logger.info(f"   Response: {response.content[:100]}...")
                    return True
                else:
                    self.logger.error(f"❌ MCP File Search: Expected MCP but got {processing_strategy}")
                    return False
            else:
                self.logger.error(f"❌ MCP File Search: Failed with status {response.status}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ MCP File Search: Error - {e}")
            return False
    
    async def test_regular_chat(self):
        """Test regular chat functionality."""
        try:
            self.logger.info("🧪 Testing Regular Chat...")
            
            # Create context
            context = {
                "user_id": "test_user",
                "message": "Hello! This is a test message.",
                "session_id": "test_session",
                "message_type": "chat",
                "metadata": {"test": True, "type": "regular_chat"}
            }
            
            # Process message
            response = await self.engine.process_message(**context)
            
            # Check response
            if response.status == "success":
                self.logger.info("✅ Regular Chat: SUCCESS")
                self.logger.info(f"   Response: {response.content[:100]}...")
                return True
            else:
                self.logger.error(f"❌ Regular Chat: Failed with status {response.status}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Regular Chat: Error - {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.engine:
            await self.engine.stop()
            self.logger.info("✅ Chatbot engine stopped")
    
    async def run_all_tests(self):
        """Run all tests."""
        self.logger.info("🚀 Starting Simple MCP Integration Tests")
        self.logger.info("=" * 60)
        
        # Setup
        if not await self.setup():
            return False
        
        # Test sequence
        tests = [
            ("Regular Chat", self.test_regular_chat),
            ("MCP File Listing", self.test_mcp_file_listing),
            ("MCP File Info", self.test_mcp_file_info),
            ("MCP File Search", self.test_mcp_file_search),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if await test_func():
                    passed += 1
                time.sleep(1)  # Small delay between tests
            except Exception as e:
                self.logger.error(f"❌ {test_name}: Unexpected error - {e}")
        
        # Summary
        self.logger.info("=" * 60)
        self.logger.info(f"📊 Test Summary: {passed}/{total} tests passed")
        
        if passed == total:
            self.logger.info("🎉 All tests passed! MCP integration is working perfectly!")
        else:
            self.logger.info("⚠️  Some tests failed. Check the logs above for details.")
        
        # Cleanup
        await self.cleanup()
        
        return passed == total


async def main():
    """Main function."""
    # Setup logging
    setup_logging(level="INFO")
    logger = get_logger(__name__)
    
    try:
        # Create and run tester
        tester = SimpleMCPTester()
        success = await tester.run_all_tests()
        
        # Exit with appropriate code
        if success:
            logger.info("\n🎉 Simple MCP Test Suite: ALL TESTS PASSED")
            sys.exit(0)
        else:
            logger.info("\n⚠️  Simple MCP Test Suite: SOME TESTS FAILED")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 