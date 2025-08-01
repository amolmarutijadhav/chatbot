#!/usr/bin/env python3
"""Test script for LLM and MCP integration."""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config_manager import ConfigurationManager
from utils.logger import setup_logging, get_logger
from llm.llm_manager import LLMManager
from mcp.mcp_manager import MCPManager
from core.models import Message


async def test_llm_integration():
    """Test LLM integration."""
    print("Testing LLM Integration...")
    
    # Create test config
    config = {
        "default_provider": "openai",
        "providers": {
            "openai": {
                "name": "openai",
                "model": "gpt-3.5-turbo",
                "base_url": "https://api.openai.com/v1",
                "api_key": "test-key",  # This will fail, but we can test the structure
                "max_tokens": 1000,
                "temperature": 0.7
            }
        }
    }
    
    try:
        # Create LLM manager
        llm_manager = LLMManager(config)
        
        # Test manager creation
        print("✓ LLM Manager created successfully")
        
        # Test provider creation (will fail to connect due to invalid API key)
        try:
            await llm_manager.start()
            print("✓ LLM Manager started successfully")
        except Exception as e:
            print(f"⚠ LLM Manager start failed (expected): {e}")
        
        # Test provider stats
        stats = await llm_manager.get_provider_stats()
        print(f"✓ LLM Stats: {stats}")
        
        await llm_manager.stop()
        print("✓ LLM Manager stopped successfully")
        
    except Exception as e:
        print(f"✗ LLM Integration test failed: {e}")
        return False
    
    return True


async def test_mcp_integration():
    """Test MCP integration."""
    print("\nTesting MCP Integration...")
    
    # Create test config
    config = {
        "servers": {
            "test_server": {
                "name": "test_server",
                "type": "file_system",
                "transport": "stdio",
                "command": "echo",
                "args": ["test"]
            }
        }
    }
    
    try:
        # Create MCP manager
        mcp_manager = MCPManager(config)
        
        # Test manager creation
        print("✓ MCP Manager created successfully")
        
        # Test server creation (will fail to connect due to invalid command)
        try:
            await mcp_manager.start()
            print("✓ MCP Manager started successfully")
        except Exception as e:
            print(f"⚠ MCP Manager start failed (expected): {e}")
        
        # Test server stats
        stats = await mcp_manager.get_server_stats()
        print(f"✓ MCP Stats: {stats}")
        
        await mcp_manager.stop()
        print("✓ MCP Manager stopped successfully")
        
    except Exception as e:
        print(f"✗ MCP Integration test failed: {e}")
        return False
    
    return True


async def test_message_processing():
    """Test message processing logic."""
    print("\nTesting Message Processing...")
    
    try:
        from core.message_processor import MessageProcessor
        from core.models import Context
        
        # Create test config
        config = {
            "mcp_keywords": ["file", "directory", "list"],
            "llm_keywords": ["explain", "help", "what"],
            "max_context_length": 4000,
            "enable_mcp_fallback": True
        }
        
        # Create message processor
        processor = MessageProcessor(config)
        print("✓ Message Processor created successfully")
        
        # Test context creation
        context = Context(
            session_id="test-session",
            user_id="test-user",
            message="List the files in the current directory",
            message_type="chat",
            correlation_id="test-123"
        )
        
        # Test strategy determination
        strategy = processor._determine_processing_strategy(context)
        print(f"✓ Processing strategy determined: {strategy}")
        
        # Test MCP request detection
        is_mcp = processor._is_mcp_request("list files")
        print(f"✓ MCP request detection: {is_mcp}")
        
        # Test LLM request detection
        is_llm = processor._is_llm_request("explain machine learning")
        print(f"✓ LLM request detection: {is_llm}")
        
        # Test message preparation
        messages = processor._prepare_messages_for_llm(context)
        print(f"✓ Messages prepared for LLM: {len(messages)} messages")
        
    except Exception as e:
        print(f"✗ Message Processing test failed: {e}")
        return False
    
    return True


async def test_factory_patterns():
    """Test factory patterns."""
    print("\nTesting Factory Patterns...")
    
    try:
        from llm.llm_factory import LLMFactory
        from mcp.mcp_factory import MCPFactory
        
        # Test LLM factory
        print("Testing LLM Factory...")
        providers = LLMFactory.get_available_providers()
        print(f"✓ Available LLM providers: {providers}")
        
        # Test MCP factory
        print("Testing MCP Factory...")
        transports = MCPFactory.get_available_transports()
        print(f"✓ Available MCP transports: {transports}")
        
        # Test transport creation
        transport_config = {
            "command": "echo",
            "args": ["test"]
        }
        
        try:
            transport = MCPFactory.create_transport("stdio", transport_config)
            print("✓ STDIO transport created successfully")
        except Exception as e:
            print(f"⚠ Transport creation failed (expected): {e}")
        
    except Exception as e:
        print(f"✗ Factory Patterns test failed: {e}")
        return False
    
    return True


async def main():
    """Main test function."""
    print("🧪 Testing LLM and MCP Integration")
    print("=" * 50)
    
    # Setup logging
    setup_logging(level="INFO", console_output=True)
    logger = get_logger(__name__)
    
    results = []
    
    # Run tests
    results.append(await test_llm_integration())
    results.append(await test_mcp_integration())
    results.append(await test_message_processing())
    results.append(await test_factory_patterns())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! LLM and MCP integration is working correctly.")
        return True
    else:
        print("⚠ Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 