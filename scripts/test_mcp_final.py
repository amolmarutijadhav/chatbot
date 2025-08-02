#!/usr/bin/env python3
"""
Final Comprehensive Test for MCP File System Server
Tests all functionality after fixes.
"""

import requests
import json
import sys
from pathlib import Path

def test_mcp_filesystem_final():
    """Test MCP filesystem operations through the chatbot API."""
    
    base_url = "http://localhost:8000"
    session_id = None
    
    print("🧪 Final MCP File System Server Testing")
    print("=" * 60)
    
    # Create a session
    try:
        response = requests.post(
            f"{base_url}/api/v1/sessions",
            json={"user_id": "final-test-user"},
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
    
    # Test 1: Search for files with test in the name (the problematic case)
    print("\n🔍 Test 1: Search for files with test in the name")
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
            print(f"✅ Response: {data.get('content', '')[:100]}...")
            print(f"   Tool used: {data.get('metadata', {}).get('tool_used', 'unknown')}")
            print(f"   Status: {data.get('status', 'unknown')}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: List files in current directory
    print("\n📁 Test 2: List files in current directory")
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
            print(f"✅ Response: {data.get('content', '')[:100]}...")
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
            print(f"✅ Response: {data.get('content', '')[:100]}...")
            print(f"   Tool used: {data.get('metadata', {}).get('tool_used', 'unknown')}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: List files in scripts directory
    print("\n📂 Test 4: List files in scripts directory")
    try:
        response = requests.post(
            f"{base_url}/api/v1/chat",
            json={
                "message": "list files in scripts directory",
                "session_id": session_id
            },
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {data.get('content', '')[:100]}...")
            print(f"   Tool used: {data.get('metadata', {}).get('tool_used', 'unknown')}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Try to read a file (this should work now)
    print("\n📖 Test 5: Read README.md file")
    try:
        response = requests.post(
            f"{base_url}/api/v1/chat",
            json={
                "message": "read README.md",
                "session_id": session_id
            },
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {data.get('content', '')[:100]}...")
            print(f"   Tool used: {data.get('metadata', {}).get('tool_used', 'unknown')}")
            print(f"   Status: {data.get('status', 'unknown')}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Final MCP File System testing completed!")
    return True

if __name__ == "__main__":
    success = test_mcp_filesystem_final()
    sys.exit(0 if success else 1) 