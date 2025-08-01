"""Main chatbot engine that orchestrates all components."""

import asyncio
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime

from .models import Message, Context, Response, Session
from .session_manager import SessionManager
from .context_manager import ContextManager
from .message_processor import MessageProcessor
from utils.logger import LoggerMixin
from utils.event_bus import publish_event

if TYPE_CHECKING:
    from llm.llm_manager import LLMManager
    from mcp.mcp_manager import MCPManager


class ChatbotEngine(LoggerMixin):
    """Main chatbot engine that orchestrates all components."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the chatbot engine."""
        self.config = config
        self.session_manager: Optional[SessionManager] = None
        self.context_manager: Optional[ContextManager] = None
        self.message_processor: Optional[MessageProcessor] = None
        self.llm_manager: Optional['LLMManager'] = None
        self.mcp_manager: Optional['MCPManager'] = None
        self.is_running = False
        
    async def start(self):
        """Start the chatbot engine."""
        try:
            self.logger.info("Starting Chatbot Engine...")
            
            # Initialize session manager
            session_config = self.config.get("session", {})
            self.session_manager = SessionManager(session_config)
            await self.session_manager.start()
            
            # Initialize context manager
            self.context_manager = ContextManager(self.session_manager)
            
            # Initialize message processor
            processor_config = self.config.get("message_processor", {})
            self.message_processor = MessageProcessor(processor_config)
            
            # Initialize LLM manager
            llm_config = self.config.get("llm", {})
            if llm_config:
                from llm.llm_manager import LLMManager
                self.llm_manager = LLMManager(llm_config)
                await self.llm_manager.start()
            
            # Initialize MCP manager
            mcp_config = self.config.get("mcp", {})
            if mcp_config:
                from mcp.mcp_manager import MCPManager
                self.mcp_manager = MCPManager(mcp_config)
                await self.mcp_manager.start()
            
            self.is_running = True
            self.logger.info("Chatbot Engine started successfully")
            
            # Publish event
            publish_event("chatbot_engine_started", {
                "timestamp": datetime.utcnow().isoformat(),
                "config": {
                    "session_enabled": self.session_manager is not None,
                    "llm_enabled": self.llm_manager is not None,
                    "mcp_enabled": self.mcp_manager is not None
                }
            })
            
        except Exception as e:
            self.logger.error(f"Failed to start Chatbot Engine: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the chatbot engine."""
        try:
            self.logger.info("Stopping Chatbot Engine...")
            
            # Stop all managers
            if self.mcp_manager:
                await self.mcp_manager.stop()
            
            if self.llm_manager:
                await self.llm_manager.stop()
            
            if self.session_manager:
                await self.session_manager.stop()
            
            self.is_running = False
            self.logger.info("Chatbot Engine stopped")
            
            # Publish event
            publish_event("chatbot_engine_stopped", {
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error stopping Chatbot Engine: {e}")
    
    async def process_message(
        self, 
        user_id: str, 
        message: str, 
        session_id: Optional[str] = None,
        message_type: str = "chat",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Response:
        """Process a user message and return a response."""
        if not self.is_running:
            raise RuntimeError("Chatbot Engine is not running")
        
        try:
            # Get or create session
            if session_id:
                session = await self.session_manager.get_session(session_id)
                if not session:
                    raise ValueError(f"Session '{session_id}' not found")
            else:
                session = await self.session_manager.create_session(user_id, metadata)
                session_id = session.session_id
            
            # Build context
            context = await self.context_manager.build_context(
                session_id=session_id,
                message=message,
                message_type=message_type,
                metadata=metadata
            )
            
            # Process message
            response = await self.message_processor.process_message(
                context=context,
                llm_manager=self.llm_manager,
                mcp_manager=self.mcp_manager
            )
            
            # Add response to context
            response_message = Message(
                content=response.content,
                role="assistant",
                metadata=response.metadata
            )
            await self.context_manager.add_message_to_context(context, response_message)
            
            self.logger.info(f"Processed message for user '{user_id}' in session '{session_id}'")
            
            # Publish event
            publish_event("message_processed", {
                "user_id": user_id,
                "session_id": session_id,
                "message_type": message_type,
                "response_length": len(response.content),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            
            # Publish error event
            publish_event("message_processing_error", {
                "user_id": user_id,
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            raise
    
    async def create_session(self, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> Session:
        """Create a new session for a user."""
        if not self.is_running:
            raise RuntimeError("Chatbot Engine is not running")
        
        return await self.session_manager.create_session(user_id, metadata)
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        if not self.is_running:
            raise RuntimeError("Chatbot Engine is not running")
        
        return await self.session_manager.get_session(session_id)
    
    async def close_session(self, session_id: str) -> bool:
        """Close a session."""
        if not self.is_running:
            raise RuntimeError("Chatbot Engine is not running")
        
        return await self.session_manager.close_session(session_id)
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        if not self.is_running:
            raise RuntimeError("Chatbot Engine is not running")
        
        return self.session_manager.get_session_stats()
    
    async def get_llm_stats(self) -> Dict[str, Any]:
        """Get LLM statistics."""
        if not self.is_running or not self.llm_manager:
            return {}
        
        return await self.llm_manager.get_provider_stats()
    
    async def get_mcp_stats(self) -> Dict[str, Any]:
        """Get MCP statistics."""
        if not self.is_running or not self.mcp_manager:
            return {}
        
        return await self.mcp_manager.get_server_stats()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components."""
        health_status = {
            "engine_running": self.is_running,
            "components": {}
        }
        
        # Check session manager
        if self.session_manager:
            health_status["components"]["session_manager"] = True
        else:
            health_status["components"]["session_manager"] = False
        
        # Check LLM manager
        if self.llm_manager:
            llm_health = await self.llm_manager.health_check()
            health_status["components"]["llm_manager"] = llm_health
        else:
            health_status["components"]["llm_manager"] = {}
        
        # Check MCP manager
        if self.mcp_manager:
            mcp_health = await self.mcp_manager.health_check()
            health_status["components"]["mcp_manager"] = mcp_health
        else:
            health_status["components"]["mcp_manager"] = {}
        
        return health_status
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        return self.config.copy()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop() 