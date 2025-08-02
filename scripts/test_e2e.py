#!/usr/bin/env python3
"""
End-to-End Testing Script for Intelligent MCP Chatbot
Tests the complete workflow from session creation to chat interaction.
"""

import requests
import json
import time
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.logger import get_logger

logger = get_logger(__name__)

class ChatbotE2ETester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if details:
            result += f" - {details}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def test_health_endpoint(self):
        """Test the health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Endpoint", True, f"Status: {data.get('status')}")
                return True
            else:
                self.log_test("Health Endpoint", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Endpoint", False, str(e))
            return False
    
    def test_stats_endpoint(self):
        """Test the stats endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/stats")
            if response.status_code == 200:
                data = response.json()
                self.log_test("Stats Endpoint", True, f"Active sessions: {data.get('active_sessions', 0)}")
                return True
            else:
                self.log_test("Stats Endpoint", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Stats Endpoint", False, str(e))
            return False
    
    def test_session_creation(self):
        """Test session creation"""
        try:
            payload = {"user_id": "e2e-test-user"}
            response = requests.post(
                f"{self.base_url}/api/v1/sessions",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get("session_id")
                self.log_test("Session Creation", True, f"Session ID: {self.session_id}")
                return True
            else:
                self.log_test("Session Creation", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Session Creation", False, str(e))
            return False
    
    def test_chat_message(self):
        """Test sending a chat message"""
        if not self.session_id:
            self.log_test("Chat Message", False, "No session ID available")
            return False
            
        try:
            payload = {
                "message": "Hello! This is an end-to-end test message. Can you respond?",
                "session_id": self.session_id
            }
            response = requests.post(
                f"{self.base_url}/api/v1/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                self.log_test("Chat Message", True, f"Response length: {len(content)} chars")
                return True
            else:
                self.log_test("Chat Message", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Chat Message", False, str(e))
            return False
    
    def test_mcp_integration(self):
        """Test MCP server integration"""
        try:
            # Test if MCP servers are available
            response = requests.get(f"{self.base_url}/api/v1/health")
            if response.status_code == 200:
                data = response.json()
                mcp_status = data.get("components", {}).get("mcp_manager", {}).get("status")
                if mcp_status == "healthy":
                    self.log_test("MCP Integration", True, "MCP Manager is healthy")
                    return True
                else:
                    self.log_test("MCP Integration", False, f"MCP Manager status: {mcp_status}")
                    return False
            else:
                self.log_test("MCP Integration", False, "Could not check MCP status")
                return False
        except Exception as e:
            self.log_test("MCP Integration", False, str(e))
            return False
    
    def test_frontend_connectivity(self):
        """Test if frontend can connect to backend"""
        try:
            response = requests.get("http://localhost:3000")
            if response.status_code == 200:
                self.log_test("Frontend Connectivity", True, "Frontend is accessible")
                return True
            else:
                self.log_test("Frontend Connectivity", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Frontend Connectivity", False, str(e))
            return False
    
    def test_websocket_endpoint(self):
        """Test WebSocket endpoint availability"""
        try:
            # Test if WebSocket endpoint is configured
            response = requests.get(f"{self.base_url}/api/v1/health")
            if response.status_code == 200:
                data = response.json()
                websocket_status = data.get("components", {}).get("websocket", {}).get("status", "unknown")
                if websocket_status in ["healthy", "enabled"]:
                    self.log_test("WebSocket Endpoint", True, "WebSocket is available")
                    return True
                else:
                    self.log_test("WebSocket Endpoint", False, f"WebSocket status: {websocket_status}")
                    return False
            else:
                self.log_test("WebSocket Endpoint", False, "Could not check WebSocket status")
                return False
        except Exception as e:
            self.log_test("WebSocket Endpoint", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all end-to-end tests"""
        print("🚀 Starting End-to-End Testing for Intelligent MCP Chatbot")
        print("=" * 60)
        
        # Test basic connectivity
        self.test_health_endpoint()
        self.test_stats_endpoint()
        
        # Test session management
        self.test_session_creation()
        
        # Test chat functionality
        self.test_chat_message()
        
        # Test MCP integration
        self.test_mcp_integration()
        
        # Test frontend connectivity
        self.test_frontend_connectivity()
        
        # Test WebSocket
        self.test_websocket_endpoint()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        print(f"Passed: {passed}/{total}")
        
        if passed == total:
            print("🎉 All tests passed! The chatbot is ready for use.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
            
        return passed == total

def main():
    """Main function"""
    tester = ChatbotE2ETester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 