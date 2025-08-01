"""Core domain models for the chatbot system."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_serializer
import uuid


class Message(BaseModel):
    """Represents a message in the conversation."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        valid_roles = ['user', 'assistant', 'system']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of {valid_roles}')
        return v
    
    @model_serializer
    def ser_model(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'role': self.role,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class Context(BaseModel):
    """Represents the context for message processing."""
    
    session_id: str
    user_id: str
    message: str
    message_type: str = "chat"  # chat, mcp_request, system
    message_history: List[Message] = Field(default_factory=list)
    mcp_context: Dict[str, Any] = Field(default_factory=dict)
    llm_context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('message_type')
    @classmethod
    def validate_message_type(cls, v):
        valid_types = ['chat', 'mcp_request', 'system']
        if v not in valid_types:
            raise ValueError(f'Message type must be one of {valid_types}')
        return v
    
    def add_message(self, message: Message):
        """Add a message to the history."""
        self.message_history.append(message)
    
    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """Get the most recent messages."""
        return self.message_history[-count:]
    
    def set_metadata(self, key: str, value: Any):
        """Set metadata value."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)
    
    @model_serializer
    def ser_model(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'message': self.message,
            'message_type': self.message_type,
            'message_history': [msg.model_dump() for msg in self.message_history],
            'mcp_context': self.mcp_context,
            'llm_context': self.llm_context,
            'metadata': self.metadata,
            'correlation_id': self.correlation_id,
            'timestamp': self.timestamp.isoformat()
        }


class Response(BaseModel):
    """Represents a response from the chatbot."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    status: str = "success"  # success, error, partial
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time: Optional[float] = None
    correlation_id: Optional[str] = None
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['success', 'error', 'partial']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of {valid_statuses}')
        return v
    
    def is_success(self) -> bool:
        """Check if response is successful."""
        return self.status == "success"
    
    def is_error(self) -> bool:
        """Check if response has an error."""
        return self.status == "error"
    
    def set_metadata(self, key: str, value: Any):
        """Set metadata value."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)
    
    @model_serializer
    def ser_model(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'status': self.status,
            'error': self.error,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'processing_time': self.processing_time,
            'correlation_id': self.correlation_id
        }


class Session(BaseModel):
    """Represents a user session."""
    
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = Field(default_factory=dict)
    mcp_servers: List[str] = Field(default_factory=list)
    llm_provider: str = "default"
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def update_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def add_mcp_server(self, server_name: str):
        """Add an MCP server to the session."""
        if server_name not in self.mcp_servers:
            self.mcp_servers.append(server_name)
    
    def remove_mcp_server(self, server_name: str):
        """Remove an MCP server from the session."""
        if server_name in self.mcp_servers:
            self.mcp_servers.remove(server_name)
    
    def set_context(self, key: str, value: Any):
        """Set context value."""
        self.context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context value."""
        return self.context.get(key, default)
    
    def set_metadata(self, key: str, value: Any):
        """Set metadata value."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)
    
    def is_expired(self, timeout_seconds: int = 3600) -> bool:
        """Check if session is expired."""
        if not self.is_active:
            return True
        
        time_diff = (datetime.utcnow() - self.last_activity).total_seconds()
        return time_diff > timeout_seconds
    
    @model_serializer
    def ser_model(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'context': self.context,
            'mcp_servers': self.mcp_servers,
            'llm_provider': self.llm_provider,
            'is_active': self.is_active,
            'metadata': self.metadata
        }


class ChatRequest(BaseModel):
    """Request model for chat API."""
    
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    message_type: str = "chat"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()
    
    @field_validator('message_type')
    @classmethod
    def validate_message_type(cls, v):
        valid_types = ['chat', 'mcp_request', 'system']
        if v not in valid_types:
            raise ValueError(f'Message type must be one of {valid_types}')
        return v


class ChatResponse(BaseModel):
    """Response model for chat API."""
    
    response: Response
    session_id: str
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @model_serializer
    def ser_model(self) -> Dict[str, Any]:
        return {
            'response': self.response.model_dump(),
            'session_id': self.session_id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat()
        }


class SessionRequest(BaseModel):
    """Request model for session management."""
    
    user_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    """Response model for session management."""
    
    session: Session
    success: bool = True
    message: str = "Session created successfully"
    
    @model_serializer
    def ser_model(self) -> Dict[str, Any]:
        return {
            'session': self.session.model_dump(),
            'success': self.success,
            'message': self.message
        }


class HealthCheck(BaseModel):
    """Health check response model."""
    
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    components: Dict[str, str] = Field(default_factory=dict)
    
    @model_serializer
    def ser_model(self) -> Dict[str, Any]:
        return {
            'status': self.status,
            'timestamp': self.timestamp.isoformat(),
            'version': self.version,
            'components': self.components
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    @model_serializer
    def ser_model(self) -> Dict[str, Any]:
        return {
            'error': self.error,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id,
            'details': self.details
        } 