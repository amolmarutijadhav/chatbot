"""API route handlers for the Intelligent MCP Chatbot."""

import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi.util import get_remote_address

from .models import (
    ChatRequest, ChatResponse, SessionRequest, SessionResponse,
    UserRequest, UserResponse, HealthResponse, StatsResponse,
    ErrorResponse
)
from .auth import get_current_user, TokenData, get_user_manager
from core.chatbot_engine import ChatbotEngine
from utils.logger import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter()


# Global chatbot engine instance
_chatbot_engine: Optional[ChatbotEngine] = None


def get_chatbot_engine() -> ChatbotEngine:
    """Get chatbot engine instance."""
    global _chatbot_engine
    if _chatbot_engine is None:
        raise RuntimeError("Chatbot engine not initialized. Call init_chatbot_engine() first.")
    return _chatbot_engine


def init_chatbot_engine(engine: ChatbotEngine):
    """Initialize chatbot engine."""
    global _chatbot_engine
    _chatbot_engine = engine
    logger.info("Chatbot engine initialized for API")


@router.post("/chat", response_model=ChatResponse, summary="Send a chat message")
async def chat_endpoint(
    request: ChatRequest,
    current_user: TokenData = Depends(get_current_user),
    req: Request = None
):
    """Send a chat message and get AI response."""
    try:
        start_time = time.time()
        engine = get_chatbot_engine()
        
        # Process message
        response = await engine.process_message(
            user_id=current_user.user_id,
            message=request.message,
            session_id=request.session_id,
            message_type=request.message_type,
            metadata=request.metadata
        )
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Create response
        chat_response = ChatResponse(
            content=response.content,
            session_id=response.session_id,
            message_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            status=response.status,
            metadata=response.metadata,
            processing_time_ms=processing_time_ms
        )
        
        logger.info(
            f"Chat message processed successfully",
            extra={
                "user_id": current_user.user_id,
                "session_id": response.session_id,
                "processing_time_ms": processing_time_ms,
                "request_id": getattr(req.state, 'request_id', None)
            }
        )
        
        return chat_response
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.post("/sessions", response_model=SessionResponse, summary="Create a new session")
async def create_session(
    session_request: SessionRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Create a new chat session."""
    try:
        engine = get_chatbot_engine()
        
        # Create session
        session = await engine.create_session(
            user_id=session_request.user_id or current_user.user_id,
            metadata=session_request.metadata
        )
        
        # Create response
        session_response = SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            created_at=session.created_at,
            last_activity=session.last_activity,
            message_count=session.message_count,
            metadata=session.metadata,
            status=session.status
        )
        
        logger.info(f"Session created: {session.session_id}")
        return session_response
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=SessionResponse, summary="Get session details")
async def get_session(
    session_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Get session details by ID."""
    try:
        engine = get_chatbot_engine()
        
        # Get session
        session = await engine.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Create response
        session_response = SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            created_at=session.created_at,
            last_activity=session.last_activity,
            message_count=session.message_count,
            metadata=session.metadata,
            status=session.status
        )
        
        return session_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )


@router.delete("/sessions/{session_id}", summary="Close a session")
async def close_session(
    session_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Close a chat session."""
    try:
        engine = get_chatbot_engine()
        
        # Close session
        success = await engine.close_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        logger.info(f"Session closed: {session_id}")
        return {"message": "Session closed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close session: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check():
    """Get system health status."""
    try:
        # Get system stats
        import psutil
        memory_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Create a simple health response
        health_response = HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            uptime_seconds=time.time(),
            components={
                "session_manager": {"status": "healthy", "active_sessions": 0},
                "llm_manager": {"status": "healthy", "providers": 0},
                "mcp_manager": {"status": "healthy", "servers": 0},
                "api_server": {"status": "healthy", "endpoints": 8}
            },
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage
        )
        
        return health_response
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/stats", response_model=StatsResponse, summary="Get system statistics")
async def get_stats():
    """Get system statistics."""
    try:
        engine = get_chatbot_engine()
        
        # Get various stats
        session_stats = await engine.get_session_stats()
        llm_stats = await engine.get_llm_stats()
        mcp_stats = await engine.get_mcp_stats()
        
        # Create response
        stats_response = StatsResponse(
            total_sessions=session_stats.get("total_sessions", 0),
            active_sessions=session_stats.get("active_sessions", 0),
            total_messages=session_stats.get("total_messages", 0),
            llm_providers=llm_stats.get("providers", {}),
            mcp_servers=mcp_stats.get("servers", {}),
            average_response_time_ms=session_stats.get("average_response_time_ms", 0.0),
            timestamp=datetime.utcnow()
        )
        
        return stats_response
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.post("/users", response_model=UserResponse, summary="Create a new user")
async def create_user(user_request: UserRequest):
    """Create a new user account."""
    try:
        user_manager = get_user_manager()
        
        # Create user
        user = user_manager.create_user(
            email=user_request.email,
            name=user_request.name
        )
        
        # Create response
        user_response = UserResponse(
            user_id=user["user_id"],
            email=user["email"],
            name=user["name"],
            created_at=user["created_at"],
            last_login=None,
            active_sessions=0,
            metadata=user["metadata"]
        )
        
        logger.info(f"User created: {user['user_id']}")
        return user_response
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=UserResponse, summary="Get user details")
async def get_user(
    user_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Get user details by ID."""
    try:
        user_manager = get_user_manager()
        
        # Get user
        user = user_manager.get_user(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get active sessions count
        engine = get_chatbot_engine()
        session_stats = await engine.get_session_stats()
        active_sessions = session_stats.get("active_sessions", 0)
        
        # Create response
        user_response = UserResponse(
            user_id=user["user_id"],
            email=user["email"],
            name=user["name"],
            created_at=user["created_at"],
            last_login=user.get("last_login"),
            active_sessions=active_sessions,
            metadata=user["metadata"]
        )
        
        return user_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )


@router.get("/", summary="API root")
async def root():
    """API root endpoint."""
    return {
        "message": "Intelligent MCP Chatbot API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "chat": "/chat",
            "sessions": "/sessions",
            "health": "/health",
            "stats": "/stats",
            "users": "/users",
            "docs": "/docs"
        }
    } 