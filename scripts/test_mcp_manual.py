#!/usr/bin/env python3
"""
Manual Test Script for MCP Integration
Interactive testing of MCP functionality through the API
"""

import requests
import json
import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.logger import setup_logging, get_logger


class MCPManualTester:
    """Manual tester for MCP integration."""
    
    def __init__(self):
        """Initialize the tester."""
        self.logger = get_logger(__name__)
        self.base_url = "http://localhost:8000"
        self.session_id = None
        
    def create_session(self):
        """Create a new session."""
        try:
            session_data = {
                "user_id": "manual_test_user",
                "metadata": {"test": True, "manual": True}
            }
            response = requests.post(f"{self.base_url}/sessions", json=session_data)
            
            if response.status_code == 200:
                session_response = response.json()
                self.session_id = session_response.get("session", {}).get("session_id")
                self.logger.info(f"✅ Session created: {self.session_id}")
                return True
            else:
                self.logger.error(f"❌ Failed to create session: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Error creating session: {e}")
            return False
    
    def send_message(self, message: str, message_type: str = "chat"):
        """Send a message and get response."""
        if not self.session_id:
            self.logger.error("❌ No session available. Create session first.")
            return None
            
        try:
            chat_data = {
                "message": message,
                "session_id": self.session_id,
                "message_type": message_type,
                "metadata": {"test": True, "manual": True}
            }
            
            self.logger.info(f"📤 Sending: {message}")
            response = requests.post(f"{self.base_url}/chat", json=chat_data, timeout=30)
            
            if response.status_code == 200:
                chat_response = response.json()
                content = chat_response.get("content", "")
                status = chat_response.get("status", "")
                metadata = chat_response.get("metadata", {})
                processing_time = chat_response.get("processing_time_ms", 0)
                
                processing_strategy = metadata.get("processing_strategy", "")
                tool_used = metadata.get("tool_used", "")
                
                self.logger.info(f"📥 Response ({processing_time}ms):")
                self.logger.info(f"   Status: {status}")
                self.logger.info(f"   Strategy: {processing_strategy}")
                if tool_used:
                    self.logger.info(f"   Tool: {tool_used}")
                self.logger.info(f"   Content: {content}")
                
                return chat_response
            else:
                self.logger.error(f"❌ Failed to send message: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"❌ Error sending message: {e}")
            return None
    
    def show_system_stats(self):
        """Show system statistics."""
        try:
            response = requests.get(f"{self.base_url}/stats")
            
            if response.status_code == 200:
                stats_data = response.json()
                self.logger.info("📊 System Statistics:")
                
                # MCP Stats
                mcp_stats = stats_data.get("mcp_stats", {})
                total_servers = mcp_stats.get("total_servers", 0)
                connected_servers = mcp_stats.get("connected_servers", 0)
                self.logger.info(f"   MCP Servers: {connected_servers}/{total_servers} connected")
                
                # LLM Stats
                llm_stats = stats_data.get("llm_stats", {})
                total_providers = llm_stats.get("total_providers", 0)
                connected_providers = llm_stats.get("connected_providers", 0)
                self.logger.info(f"   LLM Providers: {connected_providers}/{total_providers} connected")
                
                # Session Stats
                session_stats = stats_data.get("session_stats", {})
                total_sessions = session_stats.get("total_sessions", 0)
                active_sessions = session_stats.get("active_sessions", 0)
                self.logger.info(f"   Sessions: {active_sessions}/{total_sessions} active")
                
            else:
                self.logger.error(f"❌ Failed to get stats: {response.status_code}")
        except Exception as e:
            self.logger.error(f"❌ Error getting stats: {e}")
    
    def cleanup_session(self):
        """Clean up the session."""
        if not self.session_id:
            self.logger.info("ℹ️  No session to cleanup")
            return
            
        try:
            response = requests.delete(f"{self.base_url}/sessions/{self.session_id}")
            
            if response.status_code in [200, 204]:
                self.logger.info("✅ Session cleaned up successfully")
                self.session_id = None
            else:
                self.logger.error(f"❌ Failed to cleanup session: {response.status_code}")
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up session: {e}")


def main():
    """Main function."""
    setup_logging(level="INFO")
    logger = get_logger(__name__)
    
    tester = MCPManualTester()
    
    print("🚀 MCP Manual Test Interface")
    print("=" * 50)
    print("Commands:")
    print("  create    - Create a new session")
    print("  send <msg> - Send a message")
    print("  stats     - Show system statistics")
    print("  cleanup   - Clean up session")
    print("  quit      - Exit")
    print("=" * 50)
    
    # Create session automatically
    if not tester.create_session():
        logger.error("Failed to create session. Exiting.")
        return
    
    while True:
        try:
            command = input("\n🤖 Enter command: ").strip().lower()
            
            if command == "quit" or command == "exit":
                break
            elif command == "create":
                tester.create_session()
            elif command.startswith("send "):
                message = command[5:]  # Remove "send " prefix
                if message:
                    tester.send_message(message)
                else:
                    print("❌ Please provide a message to send")
            elif command == "stats":
                tester.show_system_stats()
            elif command == "cleanup":
                tester.cleanup_session()
            elif command == "help":
                print("Commands: create, send <msg>, stats, cleanup, quit")
            else:
                print("❌ Unknown command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\n⏹️  Interrupted by user")
            break
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    # Cleanup
    tester.cleanup_session()
    print("👋 Goodbye!")


if __name__ == "__main__":
    main() 