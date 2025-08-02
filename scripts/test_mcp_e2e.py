#!/usr/bin/env python3
"""
End-to-End Test for MCP Integration through UI
Tests the complete flow from frontend to backend with MCP functionality
"""

import asyncio
import json
import time
import requests
from typing import Dict, Any, List
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.config_manager import ConfigurationManager
from utils.logger import setup_logging, get_logger


class MCPE2ETester:
    """End-to-end tester for MCP integration."""
    
    def __init__(self):
        """Initialize the tester."""
        self.logger = get_logger(__name__)
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.session_id = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        self.logger.info(f"{status} {test_name}")
        if details:
            self.logger.info(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        })
    
    def test_backend_health(self) -> bool:
        """Test backend health endpoint."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.log_test("Backend Health Check", True, f"Status: {health_data.get('status')}")
                return True
            else:
                self.log_test("Backend Health Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Error: {str(e)}")
            return False
    
    def test_frontend_availability(self) -> bool:
        """Test frontend availability."""
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                self.log_test("Frontend Availability", True, "Frontend is accessible")
                return True
            else:
                self.log_test("Frontend Availability", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Frontend Availability", False, f"Error: {str(e)}")
            return False
    
    def test_session_creation(self) -> bool:
        """Test session creation."""
        try:
            session_data = {
                "user_id": "e2e_test_user",
                "metadata": {"test": True, "mcp_e2e": True}
            }
            response = requests.post(
                f"{self.base_url}/sessions",
                json=session_data,
                timeout=10
            )
            
            if response.status_code == 200:
                session_response = response.json()
                self.session_id = session_response.get("session", {}).get("session_id")
                self.log_test("Session Creation", True, f"Session ID: {self.session_id}")
                return True
            else:
                self.log_test("Session Creation", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Session Creation", False, f"Error: {str(e)}")
            return False
    
    def test_regular_chat(self) -> bool:
        """Test regular chat functionality."""
        try:
            chat_data = {
                "message": "Hello! This is a test message.",
                "session_id": self.session_id,
                "message_type": "chat",
                "metadata": {"test": True, "type": "regular_chat"}
            }
            
            response = requests.post(
                f"{self.base_url}/chat",
                json=chat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                chat_response = response.json()
                content = chat_response.get("content", "")
                self.log_test("Regular Chat", True, f"Response length: {len(content)} chars")
                return True
            else:
                self.log_test("Regular Chat", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Regular Chat", False, f"Error: {str(e)}")
            return False
    
    def test_mcp_file_listing(self) -> bool:
        """Test MCP file listing functionality."""
        try:
            chat_data = {
                "message": "List the files in the current directory",
                "session_id": self.session_id,
                "message_type": "chat",
                "metadata": {"test": True, "type": "mcp_file_listing"}
            }
            
            response = requests.post(
                f"{self.base_url}/chat",
                json=chat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                chat_response = response.json()
                content = chat_response.get("content", "")
                status = chat_response.get("status", "")
                
                # Check if MCP was used
                metadata = chat_response.get("metadata", {})
                processing_strategy = metadata.get("processing_strategy", "")
                tool_used = metadata.get("tool_used", "")
                
                if "mcp" in processing_strategy.lower() or tool_used == "list_files":
                    self.log_test("MCP File Listing", True, 
                                f"Strategy: {processing_strategy}, Tool: {tool_used}")
                    return True
                else:
                    self.log_test("MCP File Listing", False, 
                                f"Expected MCP but got: {processing_strategy}")
                    return False
            else:
                self.log_test("MCP File Listing", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("MCP File Listing", False, f"Error: {str(e)}")
            return False
    
    def test_mcp_file_info(self) -> bool:
        """Test MCP file info functionality."""
        try:
            chat_data = {
                "message": "Get information about the README.md file",
                "session_id": self.session_id,
                "message_type": "chat",
                "metadata": {"test": True, "type": "mcp_file_info"}
            }
            
            response = requests.post(
                f"{self.base_url}/chat",
                json=chat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                chat_response = response.json()
                content = chat_response.get("content", "")
                metadata = chat_response.get("metadata", {})
                processing_strategy = metadata.get("processing_strategy", "")
                tool_used = metadata.get("tool_used", "")
                
                if "mcp" in processing_strategy.lower() or tool_used == "file_info":
                    self.log_test("MCP File Info", True, 
                                f"Strategy: {processing_strategy}, Tool: {tool_used}")
                    return True
                else:
                    self.log_test("MCP File Info", False, 
                                f"Expected MCP but got: {processing_strategy}")
                    return False
            else:
                self.log_test("MCP File Info", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("MCP File Info", False, f"Error: {str(e)}")
            return False
    
    def test_mcp_file_search(self) -> bool:
        """Test MCP file search functionality."""
        try:
            chat_data = {
                "message": "Search for files containing 'test' in the name",
                "session_id": self.session_id,
                "message_type": "chat",
                "metadata": {"test": True, "type": "mcp_file_search"}
            }
            
            response = requests.post(
                f"{self.base_url}/chat",
                json=chat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                chat_response = response.json()
                content = chat_response.get("content", "")
                metadata = chat_response.get("metadata", {})
                processing_strategy = metadata.get("processing_strategy", "")
                tool_used = metadata.get("tool_used", "")
                
                if "mcp" in processing_strategy.lower() or tool_used == "search_files":
                    self.log_test("MCP File Search", True, 
                                f"Strategy: {processing_strategy}, Tool: {tool_used}")
                    return True
                else:
                    self.log_test("MCP File Search", False, 
                                f"Expected MCP but got: {processing_strategy}")
                    return False
            else:
                self.log_test("MCP File Search", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("MCP File Search", False, f"Error: {str(e)}")
            return False
    
    def test_system_stats(self) -> bool:
        """Test system statistics endpoint."""
        try:
            response = requests.get(f"{self.base_url}/stats", timeout=10)
            
            if response.status_code == 200:
                stats_data = response.json()
                mcp_stats = stats_data.get("mcp_stats", {})
                total_servers = mcp_stats.get("total_servers", 0)
                connected_servers = mcp_stats.get("connected_servers", 0)
                
                self.log_test("System Stats", True, 
                            f"MCP Servers: {connected_servers}/{total_servers} connected")
                return True
            else:
                self.log_test("System Stats", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("System Stats", False, f"Error: {str(e)}")
            return False
    
    def test_session_cleanup(self) -> bool:
        """Test session cleanup."""
        if not self.session_id:
            self.log_test("Session Cleanup", True, "No session to cleanup")
            return True
            
        try:
            response = requests.delete(
                f"{self.base_url}/sessions/{self.session_id}",
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                self.log_test("Session Cleanup", True, "Session closed successfully")
                return True
            else:
                self.log_test("Session Cleanup", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Session Cleanup", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all end-to-end tests."""
        self.logger.info("🚀 Starting MCP End-to-End Tests")
        self.logger.info("=" * 60)
        
        # Test sequence
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Frontend Availability", self.test_frontend_availability),
            ("Session Creation", self.test_session_creation),
            ("Regular Chat", self.test_regular_chat),
            ("MCP File Listing", self.test_mcp_file_listing),
            ("MCP File Info", self.test_mcp_file_info),
            ("MCP File Search", self.test_mcp_file_search),
            ("System Stats", self.test_system_stats),
            ("Session Cleanup", self.test_session_cleanup),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.log_test(test_name, False, f"Unexpected error: {str(e)}")
        
        # Summary
        self.logger.info("=" * 60)
        self.logger.info(f"📊 Test Summary: {passed}/{total} tests passed")
        
        if passed == total:
            self.logger.info("🎉 All tests passed! MCP integration is working perfectly!")
        else:
            self.logger.info("⚠️  Some tests failed. Check the logs above for details.")
        
        return {
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": total - passed,
            "success_rate": (passed / total) * 100 if total > 0 else 0,
            "test_results": self.test_results
        }


def main():
    """Main function."""
    # Setup logging
    setup_logging(level="INFO")
    logger = get_logger(__name__)
    
    try:
        # Create and run tester
        tester = MCPE2ETester()
        results = tester.run_all_tests()
        
        # Print detailed results
        logger.info("\n📋 Detailed Test Results:")
        for result in results["test_results"]:
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} {result['test']}: {result['details']}")
        
        # Exit with appropriate code
        if results["passed_tests"] == results["total_tests"]:
            logger.info("\n🎉 E2E Test Suite: ALL TESTS PASSED")
            sys.exit(0)
        else:
            logger.info(f"\n⚠️  E2E Test Suite: {results['failed_tests']} TESTS FAILED")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 