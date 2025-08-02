"""WebSocket implementation for real-time chat functionality."""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState

from .models import WebSocketMessage
from .auth import get_current_user, TokenData
from core.chatbot_engine import ChatbotEngine
from utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, str] = {}  # user_id -> connection_id
    
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """Connect a new WebSocket client."""
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        self.user_connections[user_id] = connection_id
        
        logger.info(f"WebSocket connected: {connection_id} for user: {user_id}")
        return connection_id
    
    def disconnect(self, connection_id: str, user_id: str):
        """Disconnect a WebSocket client."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        
        logger.info(f"WebSocket disconnected: {connection_id} for user: {user_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], user_id: str):
        """Send message to specific user."""
        connection_id = self.user_connections.get(user_id)
        if connection_id and connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending message to {user_id}: {e}")
                    self.disconnect(connection_id, user_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        disconnected = []
        
        for connection_id, websocket in self.active_connections.items():
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to {connection_id}: {e}")
                    disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            user_id = None
            for uid, cid in self.user_connections.items():
                if cid == connection_id:
                    user_id = uid
                    break
            if user_id:
                self.disconnect(connection_id, user_id)


# Global connection manager
manager = ConnectionManager()


async def get_user_from_token(websocket: WebSocket) -> Optional[str]:
    """Extract user ID from WebSocket query parameters or headers."""
    try:
        # Try to get user_id from query parameters
        user_id = websocket.query_params.get("user_id")
        if user_id:
            return user_id
        
        # Try to get from headers (for token-based auth)
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            # TODO: Implement token validation
            # For now, return a default user
            return "anonymous"
        
        return "anonymous"
    except Exception as e:
        logger.error(f"Error extracting user from WebSocket: {e}")
        return "anonymous"


async def websocket_endpoint(websocket: WebSocket, user_id: str = None):
    """WebSocket endpoint for real-time chat."""
    connection_id = None
    
    try:
        # Get user ID if not provided
        if not user_id:
            user_id = await get_user_from_token(websocket)
        
        # Connect to WebSocket
        connection_id = await manager.connect(websocket, user_id)
        
        # Send welcome message
        welcome_message = WebSocketMessage(
            type="connection_established",
            data={
                "connection_id": connection_id,
                "user_id": user_id,
                "message": "Connected to Intelligent MCP Chatbot"
            },
            timestamp=datetime.utcnow()
        )
        
        await websocket.send_text(welcome_message.json())
        
        # Get chatbot engine
        from .routes import get_chatbot_engine
        engine = get_chatbot_engine()
        
        # Handle incoming messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Create WebSocket message
                ws_message = WebSocketMessage(
                    type=message_data.get("type", "chat"),
                    data=message_data.get("data", {}),
                    timestamp=datetime.utcnow(),
                    session_id=message_data.get("session_id")
                )
                
                # Handle different message types
                if ws_message.type == "chat":
                    await handle_chat_message(websocket, ws_message, user_id, engine)
                elif ws_message.type == "ping":
                    await handle_ping_message(websocket)
                elif ws_message.type == "create_session":
                    await handle_create_session(websocket, ws_message, user_id, engine)
                else:
                    # Unknown message type
                    error_message = WebSocketMessage(
                        type="error",
                        data={
                            "error": f"Unknown message type: {ws_message.type}",
                            "message_id": str(uuid.uuid4())
                        },
                        timestamp=datetime.utcnow()
                    )
                    await websocket.send_text(error_message.json())
                
            except json.JSONDecodeError:
                # Invalid JSON
                error_message = WebSocketMessage(
                    type="error",
                    data={
                        "error": "Invalid JSON format",
                        "message_id": str(uuid.uuid4())
                    },
                    timestamp=datetime.utcnow()
                )
                await websocket.send_text(error_message.json())
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if connection_id and user_id:
            manager.disconnect(connection_id, user_id)


async def handle_chat_message(websocket: WebSocket, message: WebSocketMessage, user_id: str, engine: ChatbotEngine):
    """Handle chat message from WebSocket."""
    try:
        # Extract chat data
        chat_data = message.data
        user_message = chat_data.get("message", "")
        session_id = chat_data.get("session_id")
        message_type = chat_data.get("message_type", "chat")
        metadata = chat_data.get("metadata", {})
        
        if not user_message:
            # Send error for empty message
            error_message = WebSocketMessage(
                type="error",
                data={
                    "error": "Message cannot be empty",
                    "message_id": str(uuid.uuid4())
                },
                timestamp=datetime.utcnow()
            )
            await websocket.send_text(error_message.json())
            return
        
        # Process message with chatbot engine
        response = await engine.process_message(
            user_id=user_id,
            message=user_message,
            session_id=session_id,
            message_type=message_type,
            metadata=metadata
        )
        
        # Send response back
        response_message = WebSocketMessage(
            type="chat_response",
            data={
                "content": response.content,
                "session_id": response.session_id,
                "message_id": str(uuid.uuid4()),
                "status": response.status,
                "metadata": response.metadata
            },
            timestamp=datetime.utcnow(),
            session_id=response.session_id
        )
        
        await websocket.send_text(response_message.json())
        
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        error_message = WebSocketMessage(
            type="error",
            data={
                "error": f"Failed to process message: {str(e)}",
                "message_id": str(uuid.uuid4())
            },
            timestamp=datetime.utcnow()
        )
        await websocket.send_text(error_message.json())


async def handle_ping_message(websocket: WebSocket):
    """Handle ping message."""
    pong_message = WebSocketMessage(
        type="pong",
        data={"timestamp": datetime.utcnow().isoformat()},
        timestamp=datetime.utcnow()
    )
    await websocket.send_text(pong_message.json())


async def handle_create_session(websocket: WebSocket, message: WebSocketMessage, user_id: str, engine: ChatbotEngine):
    """Handle session creation request."""
    try:
        # Create session
        session = await engine.create_session(
            user_id=user_id,
            metadata=message.data.get("metadata", {})
        )
        
        # Send session created response
        session_message = WebSocketMessage(
            type="session_created",
            data={
                "session_id": session.session_id,
                "user_id": session.user_id,
                "created_at": session.created_at.isoformat(),
                "status": session.status
            },
            timestamp=datetime.utcnow(),
            session_id=session.session_id
        )
        
        await websocket.send_text(session_message.json())
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        error_message = WebSocketMessage(
            type="error",
            data={
                "error": f"Failed to create session: {str(e)}",
                "message_id": str(uuid.uuid4())
            },
            timestamp=datetime.utcnow()
        )
        await websocket.send_text(error_message.json()) 