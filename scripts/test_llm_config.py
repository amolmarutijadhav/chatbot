#!/usr/bin/env python3
"""
Test script to verify LLM configuration and test real LLM connectivity.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config_manager import ConfigurationManager
from utils.logger import setup_logging, get_logger
from llm.llm_manager import LLMManager
from llm.providers.openai_provider import OpenAIProvider


async def test_llm_configuration():
    """Test LLM configuration and connectivity."""
    logger = get_logger(__name__)
    
    print("🔧 Testing LLM Configuration...")
    print("=" * 50)
    
    # Initialize configuration
    config_manager = ConfigurationManager()
    
    # Setup logging
    logging_config = config_manager.get("logging", {})
    setup_logging(**logging_config)
    
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("\nTo set it up:")
        print("1. Get an API key from https://platform.openai.com/api-keys")
        print("2. Set the environment variable:")
        print("   Windows (PowerShell): $env:OPENAI_API_KEY='your-api-key-here'")
        print("   Windows (CMD): set OPENAI_API_KEY=your-api-key-here")
        print("   Linux/Mac: export OPENAI_API_KEY='your-api-key-here'")
        print("\nOr create a .env file in the project root with:")
        print("OPENAI_API_KEY=your-api-key-here")
        return False
    
    print(f"✅ API Key found: {api_key[:8]}...{api_key[-4:]}")
    
    # Get LLM configuration
    llm_config = config_manager.get_llm_config()
    print(f"✅ LLM Configuration loaded")
    print(f"   Default provider: {llm_config.get('default_provider', 'N/A')}")
    
    # Test OpenAI provider
    openai_config = llm_config.get("providers", {}).get("openai", {})
    if not openai_config:
        print("❌ OpenAI provider configuration not found!")
        return False
    
    print(f"✅ OpenAI configuration found")
    print(f"   Model: {openai_config.get('model', 'N/A')}")
    print(f"   Base URL: {openai_config.get('base_url', 'N/A')}")
    
    # Test provider connection
    try:
        print("\n🔌 Testing OpenAI connection...")
        provider = OpenAIProvider(openai_config)
        
        # Test connection
        connected = await provider.connect()
        if connected:
            print("✅ Successfully connected to OpenAI API")
            
            # Test getting models
            models = await provider.get_models()
            if models:
                print(f"✅ Available models: {len(models)}")
                # Show first few models
                for model in models[:5]:
                    print(f"   - {model}")
                if len(models) > 5:
                    print(f"   ... and {len(models) - 5} more")
            else:
                print("⚠️  No models available")
            
            # Test simple response generation
            print("\n🧪 Testing response generation...")
            test_messages = [
                {"role": "user", "content": "Hello! Please respond with 'Hello from OpenAI!' and nothing else."}
            ]
            
            response = await provider.generate_response(test_messages)
            print(f"✅ Response received: {response.strip()}")
            
            # Disconnect
            await provider.disconnect()
            print("✅ Disconnected from OpenAI API")
            
        else:
            print("❌ Failed to connect to OpenAI API")
            return False
            
    except Exception as e:
        print(f"❌ Error testing OpenAI provider: {e}")
        return False
    
    # Test LLM Manager
    try:
        print("\n🔧 Testing LLM Manager...")
        llm_manager = LLMManager(llm_config)
        await llm_manager.start()
        
        print("✅ LLM Manager started successfully")
        
        # Test manager functionality
        providers = await llm_manager.get_available_providers()
        print(f"✅ Available providers: {list(providers.keys())}")
        
        # Test response generation through manager
        print("\n🧪 Testing LLM Manager response generation...")
        response = await llm_manager.generate_response(
            "Please respond with 'Hello from LLM Manager!' and nothing else."
        )
        print(f"✅ Manager response: {response.strip()}")
        
        await llm_manager.stop()
        print("✅ LLM Manager stopped successfully")
        
    except Exception as e:
        print(f"❌ Error testing LLM Manager: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All LLM tests passed successfully!")
    print("Your chatbot is ready to use with real LLM functionality.")
    return True


async def main():
    """Main function."""
    try:
        success = await test_llm_configuration()
        if success:
            print("\n🚀 You can now run your chatbot with:")
            print("   python src/main.py demo")
            print("   python src/main.py interactive")
            print("   python src/api_main.py")
        else:
            print("\n❌ LLM configuration test failed. Please fix the issues above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 