# MCP Management Module - Implementation Plan

## 1. Implementation Overview

### 1.1 Project Structure
```
src/
├── mcp_management/                    # MCP Management Module
│   ├── __init__.py
│   ├── core/                         # Core business logic
│   │   ├── __init__.py
│   │   ├── manager.py                # Main MCP manager
│   │   ├── config_manager.py         # Configuration management
│   │   ├── event_system.py           # Event capture and management
│   │   └── health_monitor.py         # Health monitoring
│   ├── patterns/                     # Design patterns implementation
│   │   ├── __init__.py
│   │   ├── command_pattern.py        # Command pattern
│   │   ├── state_machine.py          # State machine
│   │   ├── observer_pattern.py       # Observer pattern
│   │   └── factory_pattern.py        # Factory pattern
│   ├── models/                       # Data models
│   │   ├── __init__.py
│   │   ├── server.py                 # Server models
│   │   ├── events.py                 # Event models
│   │   └── commands.py               # Command models
│   ├── api/                          # API layer
│   │   ├── __init__.py
│   │   ├── routes.py                 # REST API routes
│   │   ├── websocket.py              # WebSocket handlers
│   │   ├── models.py                 # API request/response models
│   │   └── middleware.py             # API middleware
│   ├── database/                     # Database layer
│   │   ├── __init__.py
│   │   ├── models.py                 # Database models
│   │   ├── repositories.py           # Data access layer
│   │   └── migrations.py             # Database migrations
│   └── utils/                        # Utilities
│       ├── __init__.py
│       ├── validators.py             # Input validation
│       ├── serializers.py            # Data serialization
│       └── helpers.py                # Helper functions
```

### 1.2 Implementation Phases

#### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Set up project structure
- [ ] Implement core data models
- [ ] Create database schema and migrations
- [ ] Implement basic CRUD operations
- [ ] Set up logging and error handling

#### Phase 2: Design Patterns (Week 3-4)
- [ ] Implement Command pattern for server operations
- [ ] Implement State machine for server lifecycle
- [ ] Implement Observer pattern for event system
- [ ] Implement Factory pattern for object creation
- [ ] Create unit tests for all patterns

#### Phase 3: API Layer (Week 5-6)
- [ ] Implement REST API endpoints
- [ ] Implement WebSocket for real-time updates
- [ ] Add authentication and authorization
- [ ] Implement input validation and error handling
- [ ] Create API documentation

#### Phase 4: Frontend (Week 7-8)
- [ ] Create dashboard UI components
- [ ] Implement real-time event monitoring
- [ ] Add server management controls
- [ ] Implement search and filtering
- [ ] Add responsive design

#### Phase 5: Advanced Features (Week 9-10)
- [ ] Implement bulk operations
- [ ] Add health monitoring
- [ ] Implement configuration management
- [ ] Add event export functionality
- [ ] Performance optimization

#### Phase 6: Testing & Deployment (Week 11-12)
- [ ] Comprehensive testing (unit, integration, e2e)
- [ ] Performance testing and optimization
- [ ] Security audit and fixes
- [ ] Documentation completion
- [ ] Production deployment

## 2. Detailed Implementation Steps

### 2.1 Phase 1: Core Infrastructure

#### 2.1.1 Project Setup
```bash
# Create module directory structure
mkdir -p src/mcp_management/{core,patterns,models,api,database,utils}
touch src/mcp_management/__init__.py
touch src/mcp_management/core/__init__.py
# ... create all necessary files
```

#### 2.1.2 Database Schema Implementation
```python
# src/mcp_management/database/models.py
from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MCPServer(Base):
    __tablename__ = 'mcp_servers'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(100), nullable=False)
    transport = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default='stopped')
    state = Column(String(50), nullable=False, default='stopped')
    config = Column(JSON, nullable=False, default={})
    health = Column(JSON, nullable=False, default={})
    metrics = Column(JSON, nullable=False, default={})
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### 2.1.3 Core Models Implementation
```python
# src/mcp_management/models/server.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class ServerStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"

class ServerState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    MAINTENANCE = "maintenance"

@dataclass
class ServerConfig:
    host: Optional[str] = None
    port: Optional[int] = None
    command: Optional[str] = None
    args: Optional[list] = None
    environment: Optional[Dict[str, str]] = None
    timeout: int = 30
    retry_attempts: int = 3
    health_check_interval: int = 60

@dataclass
class HealthStatus:
    is_healthy: bool = False
    last_check: Optional[datetime] = None
    error_count: int = 0
    consecutive_failures: int = 0
    response_time_ms: Optional[float] = None

@dataclass
class ServerMetrics:
    uptime_seconds: int = 0
    request_count: int = 0
    error_count: int = 0
    success_rate: float = 0.0
    avg_response_time_ms: float = 0.0
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None

@dataclass
class MCPServer:
    id: str
    name: str
    type: str
    transport: str
    status: ServerStatus
    state: ServerState
    config: ServerConfig
    health: HealthStatus
    metrics: ServerMetrics
    enabled: bool = True
    created_at: datetime = None
    updated_at: datetime = None
```

### 2.2 Phase 2: Design Patterns

#### 2.2.1 Command Pattern Implementation
```python
# src/mcp_management/patterns/command_pattern.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class CommandResult:
    success: bool
    server_id: str
    server_name: str
    command_type: str
    message: str
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    execution_time_ms: float = 0.0
    timestamp: datetime = None
    correlation_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.correlation_id is None:
            self.correlation_id = str(uuid.uuid4())

class ServerCommand(ABC):
    def __init__(self, event_capture):
        self.event_capture = event_capture
    
    @abstractmethod
    async def can_execute(self, server: MCPServer, command_data: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    async def execute(self, server: MCPServer, command_data: Dict[str, Any]) -> CommandResult:
        pass
    
    @abstractmethod
    async def undo(self, server: MCPServer, command_data: Dict[str, Any]) -> CommandResult:
        pass

class StartServerCommand(ServerCommand):
    async def can_execute(self, server: MCPServer, command_data: Dict[str, Any]) -> bool:
        return server.state in [ServerState.STOPPED, ServerState.ERROR]
    
    async def execute(self, server: MCPServer, command_data: Dict[str, Any]) -> CommandResult:
        start_time = datetime.utcnow()
        
        try:
            # Capture state change event
            await self.event_capture.capture_server_state_change(
                server_name=server.name,
                old_state=server.state.value,
                new_state=ServerState.STARTING.value,
                reason="User initiated start command"
            )
            
            server.state = ServerState.STARTING
            
            # Attempt connection with timeout
            connection_timeout = command_data.get("timeout", 30)
            success = await asyncio.wait_for(server.connect(), timeout=connection_timeout)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if success:
                server.state = ServerState.RUNNING
                server.status = ServerStatus.RUNNING
                
                await self.event_capture.capture_server_state_change(
                    server_name=server.name,
                    old_state=ServerState.STARTING.value,
                    new_state=ServerState.RUNNING.value
                )
                
                return CommandResult(
                    success=True,
                    server_id=server.id,
                    server_name=server.name,
                    command_type="StartServerCommand",
                    message=f"Server {server.name} started successfully",
                    execution_time_ms=execution_time
                )
            else:
                server.state = ServerState.ERROR
                server.status = ServerStatus.ERROR
                
                await self.event_capture.capture_server_state_change(
                    server_name=server.name,
                    old_state=ServerState.STARTING.value,
                    new_state=ServerState.ERROR.value,
                    reason="Connection failed"
                )
                
                return CommandResult(
                    success=False,
                    server_id=server.id,
                    server_name=server.name,
                    command_type="StartServerCommand",
                    message="Server connection failed",
                    error_code="CONNECTION_FAILED",
                    execution_time_ms=execution_time
                )
                
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            server.state = ServerState.ERROR
            server.status = ServerStatus.ERROR
            
            await self.event_capture.capture_error(
                server_name=server.name,
                error=e,
                context={
                    "command_type": "StartServerCommand",
                    "execution_time_ms": execution_time
                }
            )
            
            return CommandResult(
                success=False,
                server_id=server.id,
                server_name=server.name,
                command_type="StartServerCommand",
                message=f"Start failed: {str(e)}",
                error_code=type(e).__name__,
                execution_time_ms=execution_time
            )
```

#### 2.2.2 State Machine Implementation
```python
# src/mcp_management/patterns/state_machine.py
from enum import Enum
from typing import Dict, List, Set
from dataclasses import dataclass

class ServerState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    MAINTENANCE = "maintenance"

@dataclass
class StateTransition:
    from_state: ServerState
    to_state: ServerState
    trigger: str
    conditions: List[str] = None
    actions: List[str] = None

class ServerStateMachine:
    def __init__(self, server, event_capture):
        self.server = server
        self.state = ServerState.STOPPED
        self.event_capture = event_capture
        self.transitions = self._define_transitions()
    
    def _define_transitions(self) -> Dict[ServerState, Set[ServerState]]:
        return {
            ServerState.STOPPED: {ServerState.STARTING, ServerState.MAINTENANCE},
            ServerState.STARTING: {ServerState.RUNNING, ServerState.ERROR, ServerState.STOPPED},
            ServerState.RUNNING: {ServerState.STOPPING, ServerState.ERROR, ServerState.MAINTENANCE},
            ServerState.STOPPING: {ServerState.STOPPED, ServerState.ERROR},
            ServerState.ERROR: {ServerState.STOPPED, ServerState.STARTING, ServerState.MAINTENANCE},
            ServerState.MAINTENANCE: {ServerState.STOPPED, ServerState.STARTING}
        }
    
    def can_transition_to(self, new_state: ServerState) -> bool:
        return new_state in self.transitions.get(self.state, set())
    
    async def transition_to(self, new_state: ServerState, reason: str = None) -> bool:
        if self.can_transition_to(new_state):
            old_state = self.state
            self.state = new_state
            
            # Update server state
            self.server.state = new_state
            
            # Capture state change event
            await self.event_capture.capture_server_state_change(
                server_name=self.server.name,
                old_state=old_state.value,
                new_state=new_state.value,
                reason=reason
            )
            
            return True
        return False
    
    def get_available_transitions(self) -> List[ServerState]:
        return list(self.transitions.get(self.state, set()))
    
    def get_state_info(self) -> Dict[str, Any]:
        return {
            "current_state": self.state.value,
            "available_transitions": [s.value for s in self.get_available_transitions()],
            "is_stable": self.state in [ServerState.RUNNING, ServerState.STOPPED, ServerState.MAINTENANCE]
        }
```

### 2.3 Phase 3: API Layer

#### 2.3.1 REST API Routes
```python
# src/mcp_management/api/routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from .models import *
from .middleware import require_mcp_permission
from core.manager import MCPManager

router = APIRouter(prefix="/api/mcp", tags=["MCP Management"])

@router.get("/servers", response_model=ServerListResponse)
@require_mcp_permission("mcp:view_servers")
async def get_servers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """Get list of MCP servers with filtering and pagination"""
    try:
        manager = MCPManager()
        servers = await manager.get_servers(
            page=page,
            page_size=page_size,
            status=status,
            type=type,
            search=search
        )
        return servers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve servers: {str(e)}"
        )

@router.post("/servers", response_model=MCPServer)
@require_mcp_permission("mcp:manage_servers")
async def add_server(request: AddServerRequest):
    """Add a new MCP server"""
    try:
        manager = MCPManager()
        server = await manager.add_server(request)
        return server
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add server: {str(e)}"
        )

@router.get("/servers/{server_id}", response_model=ServerDetailResponse)
@require_mcp_permission("mcp:view_servers")
async def get_server(server_id: str):
    """Get detailed information about a specific server"""
    try:
        manager = MCPManager()
        server_detail = await manager.get_server_detail(server_id)
        return server_detail
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/servers/{server_id}/start")
@require_mcp_permission("mcp:manage_servers")
async def start_server(server_id: str):
    """Start a specific server"""
    try:
        manager = MCPManager()
        result = await manager.start_server(server_id)
        return {"success": result.success, "message": result.message}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/servers/{server_id}/stop")
@require_mcp_permission("mcp:manage_servers")
async def stop_server(server_id: str):
    """Stop a specific server"""
    try:
        manager = MCPManager()
        result = await manager.stop_server(server_id)
        return {"success": result.success, "message": result.message}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/servers/bulk/start")
@require_mcp_permission("mcp:bulk_operations")
async def bulk_start_servers(request: BulkOperationRequest):
    """Bulk start multiple servers"""
    try:
        manager = MCPManager()
        results = await manager.bulk_start_servers(request.server_ids)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk operation failed: {str(e)}"
        )

@router.get("/events", response_model=EventListResponse)
@require_mcp_permission("mcp:view_events")
async def get_events(
    server_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get events with filtering"""
    try:
        manager = MCPManager()
        events = await manager.get_events(
            server_id=server_id,
            event_type=event_type,
            severity=severity,
            limit=limit,
            offset=offset
        )
        return events
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve events: {str(e)}"
        )
```

#### 2.3.2 WebSocket Implementation
```python
# src/mcp_management/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import asyncio

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_data: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_data[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "subscriptions": set()
        }
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_data:
            del self.connection_data[websocket]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception:
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        if not self.active_connections:
            return
        
        message_json = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception:
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_to_subscribers(self, event_type: str, message: Dict[str, Any]):
        """Broadcast message only to subscribers of specific event type"""
        if not self.active_connections:
            return
        
        message_json = json.dumps({
            "type": event_type,
            "data": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        disconnected = []
        
        for connection in self.active_connections:
            try:
                if event_type in self.connection_data[connection]["subscriptions"]:
                    await connection.send_text(message_json)
            except Exception:
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

manager = WebSocketManager()

@router.websocket("/ws/mcp")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "subscribe":
                # Subscribe to specific event types
                event_types = message.get("events", [])
                manager.connection_data[websocket]["subscriptions"].update(event_types)
                
                await manager.send_personal_message(
                    json.dumps({
                        "type": "subscription_confirmed",
                        "events": list(event_types),
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    websocket
                )
            
            elif message["type"] == "unsubscribe":
                # Unsubscribe from specific event types
                event_types = message.get("events", [])
                manager.connection_data[websocket]["subscriptions"].difference_update(event_types)
                
                await manager.send_personal_message(
                    json.dumps({
                        "type": "unsubscription_confirmed",
                        "events": list(event_types),
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### 2.4 Phase 4: Frontend Implementation

#### 2.4.1 Main Dashboard Component
```typescript
// frontend/src/pages/MCPManagement.tsx
import React, { useState, useEffect } from 'react';
import { 
    Server, 
    Play, 
    Square, 
    Settings, 
    AlertTriangle, 
    CheckCircle, 
    XCircle, 
    RefreshCw,
    Plus,
    Search,
    Filter,
    Activity,
    BarChart3,
    Clock,
    Zap
} from 'lucide-react';
import { MCPServerStatus, MCPServerEvent } from '../types/mcp';
import { MCPService } from '../services/mcpService';
import { ServerCard } from '../components/mcp/ServerCard';
import { EventsPanel } from '../components/mcp/EventsPanel';
import { StatsCards } from '../components/mcp/StatsCards';
import { useWebSocket } from '../hooks/useWebSocket';

export const MCPManagement: React.FC = () => {
    const [servers, setServers] = useState<MCPServerStatus[]>([]);
    const [events, setEvents] = useState<MCPServerEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedServer, setSelectedServer] = useState<string | null>(null);
    const [view, setView] = useState<'dashboard' | 'list' | 'details'>('dashboard');
    const [filter, setFilter] = useState<'all' | 'running' | 'stopped' | 'error'>('all');
    const [searchTerm, setSearchTerm] = useState('');

    const mcpService = new MCPService();
    
    // WebSocket connection for real-time updates
    const { connected, lastMessage } = useWebSocket('/api/mcp/ws');

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 30000); // Refresh every 30 seconds
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (lastMessage) {
            handleWebSocketMessage(lastMessage);
        }
    }, [lastMessage]);

    const loadData = async () => {
        try {
            setLoading(true);
            const [serversData, eventsData] = await Promise.all([
                mcpService.getServers(),
                mcpService.getEvents({ limit: 50 })
            ]);
            setServers(serversData.servers);
            setEvents(eventsData.events);
        } catch (error) {
            console.error('Failed to load MCP data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleWebSocketMessage = (message: any) => {
        const { type, data } = message;
        
        switch (type) {
            case 'server_status_change':
                setServers(prev => prev.map(server => 
                    server.id === data.server_id 
                        ? { ...server, status: data.new_status }
                        : server
                ));
                break;
            
            case 'new_event':
                setEvents(prev => [data, ...prev.slice(0, 49)]); // Keep latest 50 events
                break;
            
            case 'bulk_operation_progress':
                // Update UI with bulk operation progress
                break;
        }
    };

    const filteredServers = servers.filter(server => {
        const matchesSearch = server.name.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesFilter = filter === 'all' || server.status === filter;
        return matchesSearch && matchesFilter;
    });

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center py-4">
                        <div className="flex items-center space-x-3">
                            <Server className="w-8 h-8 text-blue-600" />
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">MCP Server Management</h1>
                                <p className="text-sm text-gray-500">
                                    Manage and monitor your MCP servers
                                    {connected && <span className="text-green-500 ml-2">• Live</span>}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center space-x-3">
                            <button
                                onClick={loadData}
                                disabled={loading}
                                className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                            >
                                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                                Refresh
                            </button>
                            <button className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                                <Plus className="w-4 h-4 mr-2" />
                                Add Server
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                {/* Controls */}
                <div className="flex flex-col sm:flex-row gap-4 mb-6">
                    <div className="flex-1">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Search servers..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>
                    </div>

                    <div className="flex items-center space-x-2">
                        <Filter className="w-4 h-4 text-gray-400" />
                        <select
                            value={filter}
                            onChange={(e) => setFilter(e.target.value as any)}
                            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="all">All Servers</option>
                            <option value="running">Running</option>
                            <option value="stopped">Stopped</option>
                            <option value="error">Error</option>
                        </select>
                    </div>

                    <div className="flex bg-gray-100 rounded-lg p-1">
                        <button
                            onClick={() => setView('dashboard')}
                            className={`px-3 py-1 rounded-md text-sm font-medium ${
                                view === 'dashboard' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-600'
                            }`}
                        >
                            Dashboard
                        </button>
                        <button
                            onClick={() => setView('list')}
                            className={`px-3 py-1 rounded-md text-sm font-medium ${
                                view === 'list' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-600'
                            }`}
                        >
                            List
                        </button>
                    </div>
                </div>

                {/* Stats Cards */}
                <StatsCards servers={servers} events={events} />

                {/* Main Content */}
                {view === 'dashboard' ? (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div className="lg:col-span-2">
                            <div className="bg-white rounded-lg shadow">
                                <div className="px-6 py-4 border-b border-gray-200">
                                    <h2 className="text-lg font-semibold text-gray-900">Server Status</h2>
                                </div>
                                <div className="p-6">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {filteredServers.map((server) => (
                                            <ServerCard
                                                key={server.id}
                                                server={server}
                                                onSelect={() => setSelectedServer(server.id)}
                                                onAction={loadData}
                                            />
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="lg:col-span-1">
                            <EventsPanel events={events} />
                        </div>
                    </div>
                ) : (
                    <ServerListView servers={filteredServers} onAction={loadData} />
                )}
            </div>
        </div>
    );
};
```

## 3. Testing Strategy

### 3.1 Unit Tests
```python
# tests/test_mcp_management/test_command_pattern.py
import pytest
from unittest.mock import Mock, AsyncMock
from mcp_management.patterns.command_pattern import StartServerCommand, CommandResult
from mcp_management.models.server import MCPServer, ServerState, ServerStatus

class TestStartServerCommand:
    @pytest.fixture
    def mock_server(self):
        server = Mock(spec=MCPServer)
        server.id = "test-server-id"
        server.name = "test-server"
        server.state = ServerState.STOPPED
        server.status = ServerStatus.STOPPED
        server.connect = AsyncMock(return_value=True)
        return server
    
    @pytest.fixture
    def mock_event_capture(self):
        event_capture = Mock()
        event_capture.capture_server_state_change = AsyncMock()
        event_capture.capture_error = AsyncMock()
        return event_capture
    
    @pytest.mark.asyncio
    async def test_can_execute_when_stopped(self, mock_server, mock_event_capture):
        command = StartServerCommand(mock_event_capture)
        result = await command.can_execute(mock_server, {})
        assert result is True
    
    @pytest.mark.asyncio
    async def test_can_execute_when_running(self, mock_server, mock_event_capture):
        mock_server.state = ServerState.RUNNING
        command = StartServerCommand(mock_event_capture)
        result = await command.can_execute(mock_server, {})
        assert result is False
    
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_server, mock_event_capture):
        command = StartServerCommand(mock_event_capture)
        result = await command.execute(mock_server, {"timeout": 30})
        
        assert result.success is True
        assert result.server_id == "test-server-id"
        assert result.server_name == "test-server"
        assert result.command_type == "StartServerCommand"
        assert mock_server.state == ServerState.RUNNING
        assert mock_server.status == ServerStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_execute_connection_failure(self, mock_server, mock_event_capture):
        mock_server.connect.return_value = False
        command = StartServerCommand(mock_event_capture)
        result = await command.execute(mock_server, {"timeout": 30})
        
        assert result.success is False
        assert result.error_code == "CONNECTION_FAILED"
        assert mock_server.state == ServerState.ERROR
        assert mock_server.status == ServerStatus.ERROR
```

### 3.2 Integration Tests
```python
# tests/integration/test_mcp_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from mcp_management.api.routes import router

client = TestClient(router)

class TestMCPAPI:
    @pytest.fixture
    def mock_mcp_manager(self):
        with patch('mcp_management.api.routes.MCPManager') as mock:
            manager_instance = AsyncMock()
            mock.return_value = manager_instance
            yield manager_instance
    
    def test_get_servers_success(self, mock_mcp_manager):
        mock_mcp_manager.get_servers.return_value = {
            "servers": [],
            "total": 0,
            "page": 1,
            "page_size": 20
        }
        
        response = client.get("/api/mcp/servers")
        assert response.status_code == 200
        data = response.json()
        assert "servers" in data
        assert "total" in data
    
    def test_add_server_success(self, mock_mcp_manager):
        mock_server = {
            "id": "test-id",
            "name": "test-server",
            "type": "stdio",
            "transport": "stdio",
            "status": "stopped",
            "state": "stopped"
        }
        mock_mcp_manager.add_server.return_value = mock_server
        
        response = client.post("/api/mcp/servers", json={
            "name": "test-server",
            "type": "stdio",
            "transport": "stdio",
            "config": {}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-server"
    
    def test_start_server_success(self, mock_mcp_manager):
        mock_mcp_manager.start_server.return_value = Mock(
            success=True,
            message="Server started successfully"
        )
        
        response = client.post("/api/mcp/servers/test-id/start")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
```

## 4. Deployment Configuration

### 4.1 Docker Configuration
```dockerfile
# Dockerfile for MCP Management Module
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.2 Kubernetes Configuration
```yaml
# k8s/mcp-management-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-management
  labels:
    app: mcp-management
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-management
  template:
    metadata:
      labels:
        app: mcp-management
    spec:
      containers:
      - name: mcp-management
        image: mcp-management:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: mcp-management-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: mcp-management-secrets
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: mcp-management-service
spec:
  selector:
    app: mcp-management
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

## 5. Monitoring & Observability

### 5.1 Metrics Collection
```python
# src/mcp_management/utils/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Summary
import time

# Metrics
mcp_server_operations = Counter(
    'mcp_server_operations_total',
    'Total number of MCP server operations',
    ['operation', 'server_type', 'status']
)

mcp_server_operation_duration = Histogram(
    'mcp_server_operation_duration_seconds',
    'Duration of MCP server operations',
    ['operation', 'server_type']
)

mcp_server_health_status = Gauge(
    'mcp_server_health_status',
    'Health status of MCP servers',
    ['server_name', 'server_type']
)

mcp_events_total = Counter(
    'mcp_events_total',
    'Total number of MCP events',
    ['event_type', 'severity', 'category']
)

mcp_active_connections = Gauge(
    'mcp_active_connections',
    'Number of active MCP server connections'
)

class MetricsCollector:
    def __init__(self):
        self.start_time = time.time()
    
    def record_operation(self, operation: str, server_type: str, status: str, duration: float = None):
        mcp_server_operations.labels(
            operation=operation,
            server_type=server_type,
            status=status
        ).inc()
        
        if duration:
            mcp_server_operation_duration.labels(
                operation=operation,
                server_type=server_type
            ).observe(duration)
    
    def update_health_status(self, server_name: str, server_type: str, is_healthy: bool):
        mcp_server_health_status.labels(
            server_name=server_name,
            server_type=server_type
        ).set(1 if is_healthy else 0)
    
    def record_event(self, event_type: str, severity: str, category: str):
        mcp_events_total.labels(
            event_type=event_type,
            severity=severity,
            category=category
        ).inc()
    
    def update_connection_count(self, count: int):
        mcp_active_connections.set(count)
```

### 5.2 Health Check Endpoints
```python
# src/mcp_management/api/health.py
from fastapi import APIRouter, Depends
from typing import Dict, Any
import psutil
import asyncio

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    # Check database connectivity
    # Check Redis connectivity
    # Check MCP server connectivity
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest
    return Response(generate_latest(), media_type="text/plain")

@router.get("/system-info")
async def system_info():
    """System information for monitoring"""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "uptime": time.time() - psutil.boot_time()
    }
```

## 6. Success Criteria & Validation

### 6.1 Functional Validation
- [ ] All CRUD operations work correctly
- [ ] Real-time updates function properly
- [ ] Bulk operations complete successfully
- [ ] Error handling works as expected
- [ ] Authentication and authorization function correctly

### 6.2 Performance Validation
- [ ] Dashboard loads in < 2 seconds
- [ ] Real-time updates have < 1 second latency
- [ ] System supports 100+ concurrent servers
- [ ] Bulk operations complete within 30 seconds

### 6.3 Security Validation
- [ ] All endpoints require proper authentication
- [ ] Role-based access control works correctly
- [ ] Input validation prevents injection attacks
- [ ] Audit trail captures all actions

### 6.4 User Experience Validation
- [ ] Interface is intuitive and easy to use
- [ ] Real-time feedback is immediate and clear
- [ ] Error messages are helpful and actionable
- [ ] Responsive design works on all devices

This implementation plan provides a comprehensive roadmap for building the MCP Management Module with clear phases, detailed code examples, and validation criteria. 