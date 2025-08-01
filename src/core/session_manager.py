"""Session management for the chatbot system."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid

from .models import Session
from utils.logger import LoggerMixin
from utils.event_bus import get_event_bus, publish_event


class SessionManager(LoggerMixin):
    """Manages user sessions and their lifecycle."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.sessions: Dict[str, Session] = {}
        self.event_bus = get_event_bus()
        self.cleanup_task: Optional[asyncio.Task] = None
        self.max_sessions_per_user = config.get("max_sessions_per_user", 10)
        self.session_timeout = config.get("timeout", 3600)  # seconds
        self.cleanup_interval = config.get("cleanup_interval", 300)  # seconds
    
    async def start(self):
        """Start the session manager."""
        self.logger.info("Starting session manager")
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.logger.info("Session manager started")
    
    async def stop(self):
        """Stop the session manager."""
        self.logger.info("Stopping session manager")
        
        # Cancel cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close all sessions
        await self._close_all_sessions()
        
        self.logger.info("Session manager stopped")
    
    async def create_session(self, user_id: str, metadata: Optional[Dict] = None) -> Session:
        """Create a new session for a user."""
        # Check if user has too many sessions
        user_sessions = self._get_user_sessions(user_id)
        if len(user_sessions) >= self.max_sessions_per_user:
            # Close oldest session
            oldest_session = min(user_sessions, key=lambda s: s.created_at)
            await self.close_session(oldest_session.session_id)
        
        # Create new session
        session = Session(
            user_id=user_id,
            metadata=metadata or {}
        )
        
        self.sessions[session.session_id] = session
        
        # Publish event
        publish_event("session_created", {
            "session_id": session.session_id,
            "user_id": user_id,
            "metadata": metadata
        })
        
        self.logger.info(f"Created session {session.session_id} for user {user_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        session = self.sessions.get(session_id)
        
        if session and session.is_active:
            # Check if session is expired
            if session.is_expired(self.session_timeout):
                await self.close_session(session_id)
                return None
            
            # Update last activity
            session.update_activity()
            return session
        
        return None
    
    async def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all active sessions for a user."""
        user_sessions = self._get_user_sessions(user_id)
        
        # Filter out expired sessions
        active_sessions = []
        for session in user_sessions:
            if session.is_expired(self.session_timeout):
                await self.close_session(session.session_id)
            else:
                active_sessions.append(session)
        
        return active_sessions
    
    def _get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all sessions for a user (including expired)."""
        return [s for s in self.sessions.values() if s.user_id == user_id]
    
    async def close_session(self, session_id: str) -> bool:
        """Close a session."""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        session.is_active = False
        
        # Publish event
        publish_event("session_closed", {
            "session_id": session_id,
            "user_id": session.user_id,
            "duration": (datetime.utcnow() - session.created_at).total_seconds()
        })
        
        self.logger.info(f"Closed session {session_id}")
        return True
    
    async def update_session(self, session_id: str, updates: Dict) -> bool:
        """Update session with new data."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        # Update session fields
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)
            elif key == "context":
                session.context.update(value)
            elif key == "metadata":
                session.metadata.update(value)
        
        session.update_activity()
        
        # Publish event
        publish_event("session_updated", {
            "session_id": session_id,
            "user_id": session.user_id,
            "updates": updates
        })
        
        return True
    
    async def add_mcp_server_to_session(self, session_id: str, server_name: str) -> bool:
        """Add an MCP server to a session."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.add_mcp_server(server_name)
        session.update_activity()
        
        # Publish event
        publish_event("session_mcp_server_added", {
            "session_id": session_id,
            "user_id": session.user_id,
            "server_name": server_name
        })
        
        return True
    
    async def remove_mcp_server_from_session(self, session_id: str, server_name: str) -> bool:
        """Remove an MCP server from a session."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.remove_mcp_server(server_name)
        session.update_activity()
        
        # Publish event
        publish_event("session_mcp_server_removed", {
            "session_id": session_id,
            "user_id": session.user_id,
            "server_name": server_name
        })
        
        return True
    
    async def set_session_llm_provider(self, session_id: str, provider: str) -> bool:
        """Set the LLM provider for a session."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.llm_provider = provider
        session.update_activity()
        
        # Publish event
        publish_event("session_llm_provider_changed", {
            "session_id": session_id,
            "user_id": session.user_id,
            "provider": provider
        })
        
        return True
    
    async def _cleanup_loop(self):
        """Background task to clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        expired_sessions = []
        
        for session in self.sessions.values():
            if session.is_expired(self.session_timeout):
                expired_sessions.append(session.session_id)
        
        for session_id in expired_sessions:
            await self.close_session(session_id)
        
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    async def _close_all_sessions(self):
        """Close all active sessions."""
        active_sessions = [s.session_id for s in self.sessions.values() if s.is_active]
        
        for session_id in active_sessions:
            await self.close_session(session_id)
        
        self.logger.info(f"Closed {len(active_sessions)} active sessions")
    
    def get_session_count(self) -> int:
        """Get the total number of sessions."""
        return len(self.sessions)
    
    def get_active_session_count(self) -> int:
        """Get the number of active sessions."""
        return len([s for s in self.sessions.values() if s.is_active])
    
    def get_session_stats(self) -> Dict:
        """Get session statistics."""
        total_sessions = len(self.sessions)
        active_sessions = len([s for s in self.sessions.values() if s.is_active])
        expired_sessions = total_sessions - active_sessions
        
        # Group by user
        user_session_counts = {}
        for session in self.sessions.values():
            user_session_counts[session.user_id] = user_session_counts.get(session.user_id, 0) + 1
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "expired_sessions": expired_sessions,
            "unique_users": len(user_session_counts),
            "user_session_counts": user_session_counts
        }
    
    def __str__(self) -> str:
        return f"SessionManager(sessions={len(self.sessions)}, active={self.get_active_session_count()})"
    
    def __repr__(self) -> str:
        return f"SessionManager(sessions={list(self.sessions.keys())})" 