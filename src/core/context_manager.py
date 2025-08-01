"""Context management for message processing."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from .models import Context, Message, Session
from utils.logger import LoggerMixin
from utils.event_bus import publish_event


class ContextManager(LoggerMixin):
    """Manages context building and processing for messages."""
    
    def __init__(self, session_manager):
        self.session_manager = session_manager
    
    async def build_context(
        self, 
        session_id: str, 
        message: str, 
        message_type: str = "chat",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Context:
        """Build context for message processing."""
        start_time = datetime.utcnow()
        
        # Get or create session
        session = await self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found or expired")
        
        # Create user message
        user_message = Message(
            content=message,
            role="user",
            metadata=metadata or {}
        )
        
        # Build context
        context = Context(
            session_id=session_id,
            user_id=session.user_id,
            message=message,
            message_type=message_type,
            correlation_id=str(uuid.uuid4()),
            metadata=metadata or {}
        )
        
        # Add session context
        context.mcp_context = session.context.get("mcp", {})
        context.llm_context = session.context.get("llm", {})
        
        # Add message history from session
        message_history = session.context.get("message_history", [])
        context.message_history = [Message(**msg) for msg in message_history]
        
        # Add current message to history
        context.add_message(user_message)
        
        # Add session metadata
        context.set_metadata("session_created_at", session.created_at.isoformat())
        context.set_metadata("session_last_activity", session.last_activity.isoformat())
        context.set_metadata("session_mcp_servers", session.mcp_servers)
        context.set_metadata("session_llm_provider", session.llm_provider)
        
        # Add processing metadata
        context.set_metadata("processing_start_time", start_time.isoformat())
        context.set_metadata("context_builder", "ContextManager")
        
        # Publish event
        publish_event("context_built", {
            "session_id": session_id,
            "user_id": session.user_id,
            "message_type": message_type,
            "correlation_id": context.correlation_id,
            "processing_time": (datetime.utcnow() - start_time).total_seconds()
        })
        
        self.logger.debug(f"Built context for session {session_id}, correlation_id: {context.correlation_id}")
        return context
    
    async def update_context(self, context: Context, updates: Dict[str, Any]) -> Context:
        """Update context with new information."""
        # Update MCP context
        if "mcp_context" in updates:
            context.mcp_context.update(updates["mcp_context"])
        
        # Update LLM context
        if "llm_context" in updates:
            context.llm_context.update(updates["llm_context"])
        
        # Update metadata
        if "metadata" in updates:
            context.metadata.update(updates["metadata"])
        
        # Update session context
        await self._update_session_context(context.session_id, context)
        
        return context
    
    async def add_message_to_context(self, context: Context, message: Message) -> Context:
        """Add a message to the context."""
        context.add_message(message)
        
        # Update session context
        await self._update_session_context(context.session_id, context)
        
        return context
    
    async def get_context_summary(self, context: Context) -> Dict[str, Any]:
        """Get a summary of the context."""
        return {
            "session_id": context.session_id,
            "user_id": context.user_id,
            "message_type": context.message_type,
            "correlation_id": context.correlation_id,
            "message_count": len(context.message_history),
            "mcp_context_keys": list(context.mcp_context.keys()),
            "llm_context_keys": list(context.llm_context.keys()),
            "metadata_keys": list(context.metadata.keys()),
            "timestamp": context.timestamp.isoformat()
        }
    
    async def _update_session_context(self, session_id: str, context: Context):
        """Update session with context information."""
        session_updates = {
            "context": {
                "mcp": context.mcp_context,
                "llm": context.llm_context,
                "message_history": [msg.model_dump() for msg in context.message_history]
            }
        }
        
        await self.session_manager.update_session(session_id, session_updates)
    
    def extract_keywords(self, context: Context) -> List[str]:
        """Extract keywords from the context."""
        # Simple keyword extraction - can be enhanced with NLP
        keywords = []
        
        # Extract from current message
        words = context.message.lower().split()
        keywords.extend([word for word in words if len(word) > 3])
        
        # Extract from message history
        for message in context.message_history[-5:]:  # Last 5 messages
            words = message.content.lower().split()
            keywords.extend([word for word in words if len(word) > 3])
        
        # Remove duplicates and common words
        common_words = {'this', 'that', 'with', 'have', 'will', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'just', 'into', 'than', 'more', 'other', 'about', 'many', 'then', 'them', 'these', 'people', 'only', 'would', 'could', 'there', 'their', 'what', 'said', 'each', 'which', 'she', 'do', 'how', 'if', 'up', 'out', 'many', 'then', 'them', 'these', 'so', 'some', 'her', 'would', 'make', 'like', 'into', 'him', 'time', 'two', 'more', 'go', 'no', 'way', 'could', 'my', 'than', 'first', 'been', 'call', 'who', 'its', 'now', 'find', 'long', 'down', 'day', 'did', 'get', 'come', 'made', 'may', 'part'}
        keywords = [word for word in set(keywords) if word not in common_words]
        
        return keywords[:10]  # Return top 10 keywords
    
    def get_context_sentiment(self, context: Context) -> str:
        """Get sentiment of the context."""
        # Simple sentiment analysis - can be enhanced with proper NLP
        positive_words = {'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome', 'love', 'like', 'happy', 'pleased', 'satisfied', 'perfect', 'best', 'nice', 'beautiful', 'brilliant', 'outstanding', 'superb', 'terrific'}
        negative_words = {'bad', 'terrible', 'awful', 'horrible', 'disgusting', 'hate', 'dislike', 'angry', 'sad', 'disappointed', 'frustrated', 'worst', 'ugly', 'stupid', 'dumb', 'useless', 'worthless', 'annoying', 'irritating', 'boring'}
        
        text = context.message.lower()
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def get_context_complexity(self, context: Context) -> str:
        """Get complexity level of the context."""
        # Simple complexity analysis based on message length and vocabulary
        message_length = len(context.message.split())
        unique_words = len(set(context.message.lower().split()))
        
        if message_length > 50 or unique_words > 30:
            return "high"
        elif message_length > 20 or unique_words > 15:
            return "medium"
        else:
            return "low"
    
    def should_use_mcp(self, context: Context) -> bool:
        """Determine if MCP should be used for this context."""
        # Check if message type is MCP request
        if context.message_type == "mcp_request":
            return True
        
        # Check for MCP-related keywords
        mcp_keywords = {'file', 'read', 'write', 'list', 'directory', 'folder', 'database', 'query', 'search', 'find', 'execute', 'run', 'command', 'system', 'process', 'server', 'api', 'http', 'request', 'response'}
        
        message_lower = context.message.lower()
        mcp_keyword_count = sum(1 for keyword in mcp_keywords if keyword in message_lower)
        
        # Use MCP if there are MCP-related keywords or if explicitly requested
        return mcp_keyword_count > 0 or "mcp" in message_lower
    
    def get_suggested_mcp_servers(self, context: Context) -> List[str]:
        """Get suggested MCP servers based on context."""
        suggestions = []
        message_lower = context.message.lower()
        
        # File system related
        if any(word in message_lower for word in ['file', 'read', 'write', 'list', 'directory', 'folder']):
            suggestions.append('file_system')
        
        # Database related
        if any(word in message_lower for word in ['database', 'query', 'sql', 'table', 'data']):
            suggestions.append('database')
        
        # Web search related
        if any(word in message_lower for word in ['search', 'find', 'web', 'internet', 'google']):
            suggestions.append('web_search')
        
        # System related
        if any(word in message_lower for word in ['system', 'process', 'command', 'execute', 'run']):
            suggestions.append('system')
        
        return suggestions
    
    def __str__(self) -> str:
        return f"ContextManager(session_manager={self.session_manager})"
    
    def __repr__(self) -> str:
        return f"ContextManager(session_manager={repr(self.session_manager)})" 