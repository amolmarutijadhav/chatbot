#!/usr/bin/env python3
"""
Direct test script for MCP File System Server
Tests the filesystem operations directly.
"""

import requests
import json
import sys
from pathlib import Path

def test_mcp_filesystem():
    """Test MCP filesystem operations through the chatbot API."""
    
    base_url = "http://localhost:8000"
    session_id = None
    
    print("🧪 Testing MCP File System Server")
    print("=" * 50)
    
    # Create a session
    try:
        response = requests.post(
            f"{base_url}/api/v1/sessions",
            json={"user_id": "mcp-test-user"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            session_id = data.get("session_id")
            print(f"✅ Session created: {session_id}")
        else:
            print(f"❌ Failed to create session: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return False
    
    if not session_id:
        print("❌ No session ID available")
        return False
    
    # Test 1: List files in current directory
    print("\n📁 Test 1: List files in current directory")
    try:
        response = requests.post(
            f"{base_url}/api/v1/chat",
            json={
                "message": "list files in current directory",
                "session_id": session_id
            },
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {data.get('content', '')[:200]}...")
            print(f"   Tool used: {data.get('metadata', {}).get('tool_used', 'unknown')}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Search for test files
    print("\n🔍 Test 2: Search for test files")
    try:
        response = requests.post(
            f"{base_url}/api/v1/chat",
            json={
                "message": "search for files with test in the name",
                "session_id": session_id
            },
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {data.get('content', '')[:200]}...")
            print(f"   Tool used: {data.get('metadata', {}).get('tool_used', 'unknown')}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Search for Python files
    print("\n🐍 Test 3: Search for Python files")
    try:
        response = requests.post(
            f"{base_url}/api/v1/chat",
            json={
                "message": "search for Python files",
                "session_id": session_id
            },
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {data.get('content', '')[:200]}...")
            print(f"   Tool used: {data.get('metadata', {}).get('tool_used', 'unknown')}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: List files in tests directory
    print("\n📂 Test 4: List files in tests directory")
    try:
        response = requests.post(
            f"{base_url}/api/v1/chat",
            json={
                "message": "list files in tests directory",
                "session_id": session_id
            },
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {data.get('content', '')[:200]}...")
            print(f"   Tool used: {data.get('metadata', {}).get('tool_used', 'unknown')}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Search for specific test files
    print("\n🎯 Test 5: Search for specific test files")
    try:
        response = requests.post(
            f"{base_url}/api/v1/chat",
            json={
                "message": "search for files containing test_e2e",
                "session_id": session_id
            },
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {data.get('content', '')[:200]}...")
            print(f"   Tool used: {data.get('metadata', {}).get('tool_used', 'unknown')}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 MCP File System testing completed!")
    return True

if __name__ == "__main__":
    success = test_mcp_filesystem()
    sys.exit(0 if success else 1) 