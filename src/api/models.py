"""API data models for the Intelligent MCP Chatbot."""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message", min_length=1, max_length=10000)
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    message_type: str = Field("chat", description="Type of message (chat, command, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    content: str = Field(..., description="Assistant response content")
    session_id: str = Field(..., description="Session ID for conversation")
    message_id: str = Field(..., description="Unique message ID")
    timestamp: datetime = Field(..., description="Response timestamp")
    status: str = Field(..., description="Response status (success, error, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional response metadata")
    processing_time_ms: Optional[int] = Field(None, description="Message processing time in milliseconds")


class SessionRequest(BaseModel):
    """Request model for session creation."""
    user_id: str = Field(..., description="User identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Session metadata")


class SessionResponse(BaseModel):
    """Response model for session operations."""
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    message_count: int = Field(..., description="Number of messages in session")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Session metadata")
    status: str = Field(..., description="Session status (active, closed, etc.)")


class UserRequest(BaseModel):
    """Request model for user operations."""
    email: str = Field(..., description="User email address")
    name: Optional[str] = Field(None, description="User display name")
    metadata: Optional[Dict[str, Any]] = Field(None, description="User metadata")


class UserResponse(BaseModel):
    """Response model for user operations."""
    user_id: str = Field(..., description="User identifier")
    email: str = Field(..., description="User email address")
    name: Optional[str] = Field(None, description="User display name")
    created_at: datetime = Field(..., description="User creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    active_sessions: int = Field(..., description="Number of active sessions")
    metadata: Optional[Dict[str, Any]] = Field(None, description="User metadata")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Component health status")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")
    cpu_usage_percent: Optional[float] = Field(None, description="CPU usage percentage")


class ErrorResponse(BaseModel):
    """Response model for error endpoints."""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    timestamp: datetime = Field(..., description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")


class WebSocketMessage(BaseModel):
    """Model for WebSocket messages."""
    type: str = Field(..., description="Message type (chat, ping, pong, etc.)")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(..., description="Message timestamp")
    session_id: Optional[str] = Field(None, description="Session identifier")


class StatsResponse(BaseModel):
    """Response model for statistics endpoint."""
    total_sessions: int = Field(..., description="Total number of sessions")
    active_sessions: int = Field(..., description="Number of active sessions")
    total_messages: int = Field(..., description="Total number of messages processed")
    llm_providers: Dict[str, Dict[str, Any]] = Field(..., description="LLM provider statistics")
    mcp_servers: Dict[str, Dict[str, Any]] = Field(..., description="MCP server statistics")
    average_response_time_ms: float = Field(..., description="Average response time in milliseconds")
    timestamp: datetime = Field(..., description="Statistics timestamp") 