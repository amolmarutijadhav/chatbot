# Design Patterns

This document outlines the design patterns used in the Intelligent MCP Chatbot system, explaining their purpose, implementation, and benefits.

## 1. Factory Pattern

### Purpose
The Factory pattern is used to create objects without specifying their exact classes, providing a way to instantiate objects based on configuration or runtime conditions.

### Implementation

#### LLM Provider Factory
```python
class LLMFactory:
    """Factory for creating LLM provider instances"""
    
    @staticmethod
    def create_provider(provider_type: str, config: Dict[str, Any]) -> LLMProvider:
        if provider_type == "openai":
            return OpenAIProvider(OpenAIConfig(**config))
        elif provider_type == "anthropic":
            return AnthropicProvider(AnthropicConfig(**config))
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_type}")
```

#### Transport Factory
```python
class TransportFactory:
    """Factory for creating MCP transport instances"""
    
    def create_transport(self, transport_config: Dict[str, Any]) -> MCPTransport:
        transport_type = transport_config["type"]
        transport_class = self.registry.get_transport_class(transport_type)
        
        if not transport_class:
            raise ValueError(f"Unsupported transport type: {transport_type}")
        
        return transport_class(transport_config)
```

### Benefits
- **Flexibility**: Easy to add new providers/transports
- **Encapsulation**: Creation logic is centralized
- **Configuration-driven**: Object creation based on configuration
- **Testability**: Easy to mock and test

## 2. Strategy Pattern

### Purpose
The Strategy pattern defines a family of algorithms, encapsulates each one, and makes them interchangeable. It allows the algorithm to vary independently from clients that use it.

### Implementation

#### Server Selection Strategy
```python
class ServerSelectionStrategy(ABC):
    """Abstract strategy for MCP server selection"""
    
    @abstractmethod
    async def select_server(self, context: Context, servers: List[MCPServer]) -> MCPServer:
        pass

class RoundRobinStrategy(ServerSelectionStrategy):
    """Round-robin server selection"""
    
    def __init__(self):
        self.current_index = 0
    
    async def select_server(self, context: Context, servers: List[MCPServer]) -> MCPServer:
        if not servers:
            raise NoAvailableServersError()
        
        server = servers[self.current_index % len(servers)]
        self.current_index += 1
        return server

class LoadBasedStrategy(ServerSelectionStrategy):
    """Load-based server selection"""
    
    async def select_server(self, context: Context, servers: List[MCPServer]) -> MCPServer:
        if not servers:
            raise NoAvailableServersError()
        
        # Select server with lowest load
        return min(servers, key=lambda s: s.get_current_load())
```

#### Plugin Execution Strategy
```python
class PluginExecutionStrategy(ABC):
    """Abstract strategy for plugin execution"""
    
    @abstractmethod
    async def execute_plugins(self, plugins: List[Plugin], context: Context) -> Context:
        pass

class SequentialStrategy(PluginExecutionStrategy):
    """Execute plugins sequentially"""
    
    async def execute_plugins(self, plugins: List[Plugin], context: Context) -> Context:
        for plugin in plugins:
            if plugin.enabled:
                context = await plugin.process(context)
        return context

class ParallelStrategy(PluginExecutionStrategy):
    """Execute plugins in parallel"""
    
    async def execute_plugins(self, plugins: List[Plugin], context: Context) -> Context:
        enabled_plugins = [p for p in plugins if p.enabled]
        
        if not enabled_plugins:
            return context
        
        # Execute plugins in parallel
        tasks = [plugin.process(context) for plugin in enabled_plugins]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge results (implementation depends on plugin type)
        return self.merge_results(context, results)
```

### Benefits
- **Flexibility**: Easy to switch algorithms at runtime
- **Extensibility**: New strategies can be added without modifying existing code
- **Testability**: Each strategy can be tested independently
- **Maintainability**: Algorithm logic is separated from client code

## 3. Observer Pattern

### Purpose
The Observer pattern defines a one-to-many dependency between objects so that when one object changes state, all its dependents are notified and updated automatically.

### Implementation

#### Event System
```python
class EventBus:
    """Central event bus for system-wide communication"""
    
    def __init__(self):
        self._subscribers = defaultdict(list)
        self._event_history = []
    
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type"""
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event type"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)
    
    def publish(self, event_type: str, data: Any):
        """Publish an event to all subscribers"""
        event = Event(event_type, data, datetime.utcnow())
        self._event_history.append(event)
        
        for callback in self._subscribers[event_type]:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")

class Event:
    """Event representation"""
    
    def __init__(self, event_type: str, data: Any, timestamp: datetime):
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp
        self.id = str(uuid.uuid4())
```

#### Event Handlers
```python
class MetricsCollector:
    """Collects metrics from system events"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.metrics = {}
        self.event_bus.subscribe("mcp_request", self.handle_mcp_request)
        self.event_bus.subscribe("llm_request", self.handle_llm_request)
    
    def handle_mcp_request(self, event: Event):
        """Handle MCP request events"""
        server_name = event.data.get("server_name")
        if server_name not in self.metrics:
            self.metrics[server_name] = {"requests": 0, "errors": 0}
        
        self.metrics[server_name]["requests"] += 1
    
    def handle_llm_request(self, event: Event):
        """Handle LLM request events"""
        provider_name = event.data.get("provider_name")
        if provider_name not in self.metrics:
            self.metrics[provider_name] = {"requests": 0, "errors": 0}
        
        self.metrics[provider_name]["requests"] += 1

class HealthMonitor:
    """Monitors system health based on events"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.health_status = {}
        self.event_bus.subscribe("mcp_server_error", self.handle_server_error)
        self.event_bus.subscribe("llm_provider_error", self.handle_provider_error)
    
    def handle_server_error(self, event: Event):
        """Handle MCP server error events"""
        server_name = event.data.get("server_name")
        self.health_status[server_name] = "unhealthy"
    
    def handle_provider_error(self, event: Event):
        """Handle LLM provider error events"""
        provider_name = event.data.get("provider_name")
        self.health_status[provider_name] = "unhealthy"
```

### Benefits
- **Loose Coupling**: Components don't need to know about each other
- **Extensibility**: Easy to add new event handlers
- **Decoupling**: Event producers and consumers are separated
- **Observability**: System state changes are broadcast

## 4. Command Pattern

### Purpose
The Command pattern encapsulates a request as an object, allowing you to parameterize clients with different requests, queue operations, and support undo operations.

### Implementation

#### Message Processing Commands
```python
class MessageCommand(ABC):
    """Abstract command for message processing"""
    
    @abstractmethod
    async def execute(self, context: Context) -> Response:
        pass
    
    @abstractmethod
    def can_execute(self, context: Context) -> bool:
        pass

class ChatCommand(MessageCommand):
    """Command for processing chat messages"""
    
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
    
    def can_execute(self, context: Context) -> bool:
        return context.message_type == "chat"
    
    async def execute(self, context: Context) -> Response:
        return await self.llm_manager.generate_response(context)

class MCPCommand(MessageCommand):
    """Command for processing MCP requests"""
    
    def __init__(self, mcp_manager: MCPServerManager):
        self.mcp_manager = mcp_manager
    
    def can_execute(self, context: Context) -> bool:
        return context.message_type == "mcp_request"
    
    async def execute(self, context: Context) -> Response:
        return await self.mcp_manager.process_request(context)

class CommandInvoker:
    """Invokes commands based on context"""
    
    def __init__(self):
        self.commands: List[MessageCommand] = []
    
    def add_command(self, command: MessageCommand):
        """Add a command to the invoker"""
        self.commands.append(command)
    
    async def execute(self, context: Context) -> Response:
        """Execute the appropriate command for the context"""
        for command in self.commands:
            if command.can_execute(context):
                return await command.execute(context)
        
        raise NoSuitableCommandError(f"No suitable command for context: {context}")
```

### Benefits
- **Flexibility**: Easy to add new command types
- **Extensibility**: Commands can be combined and composed
- **Testability**: Each command can be tested independently
- **Undo Support**: Commands can support undo operations

## 5. Singleton Pattern

### Purpose
The Singleton pattern ensures a class has only one instance and provides a global point of access to it.

### Implementation

#### Configuration Manager
```python
class ConfigurationManager:
    """Singleton for managing system configuration"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.config = {}
            self.load_configuration()
            self.initialized = True
    
    def load_configuration(self):
        """Load configuration from files and environment"""
        # Load from YAML files
        config_files = [
            "config/chatbot_config.yaml",
            "config/mcp_servers.yaml",
            "config/plugins.yaml"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    file_config = yaml.safe_load(f)
                    self.config.update(file_config)
        
        # Override with environment variables
        self._load_from_environment()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
```

#### Transport Registry
```python
class TransportRegistry:
    """Singleton registry for transport types"""
    
    _instance = None
    _transports: Dict[str, Type[MCPTransport]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register_transport(self, transport_type: str, transport_class: Type[MCPTransport]):
        """Register a transport type"""
        self._transports[transport_type] = transport_class
    
    def get_transport_class(self, transport_type: str) -> Optional[Type[MCPTransport]]:
        """Get transport class by type"""
        return self._transports.get(transport_type)
    
    def list_transports(self) -> List[str]:
        """List all registered transport types"""
        return list(self._transports.keys())
```

### Benefits
- **Global Access**: Single point of access to shared resources
- **Resource Management**: Efficient resource usage
- **State Management**: Centralized state management
- **Configuration**: Global configuration management

## 6. Builder Pattern

### Purpose
The Builder pattern constructs complex objects step by step, allowing you to produce different types and representations of an object using the same construction code.

### Implementation

#### Context Builder
```python
class ContextBuilder:
    """Builder for creating context objects"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset the builder state"""
        self._context = {
            "session_id": None,
            "user_id": None,
            "message": None,
            "message_type": None,
            "metadata": {},
            "mcp_context": {},
            "llm_context": {}
        }
        return self
    
    def with_session(self, session_id: str, user_id: str):
        """Set session information"""
        self._context["session_id"] = session_id
        self._context["user_id"] = user_id
        return self
    
    def with_message(self, message: str, message_type: str = "chat"):
        """Set message information"""
        self._context["message"] = message
        self._context["message_type"] = message_type
        return self
    
    def with_metadata(self, key: str, value: Any):
        """Add metadata"""
        self._context["metadata"][key] = value
        return self
    
    def with_mcp_context(self, context: Dict[str, Any]):
        """Set MCP context"""
        self._context["mcp_context"].update(context)
        return self
    
    def with_llm_context(self, context: Dict[str, Any]):
        """Set LLM context"""
        self._context["llm_context"].update(context)
        return self
    
    def build(self) -> Context:
        """Build the context object"""
        context = Context(**self._context)
        self.reset()
        return context
```

#### Response Builder
```python
class ResponseBuilder:
    """Builder for creating response objects"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset the builder state"""
        self._response = {
            "content": None,
            "metadata": {},
            "status": "success",
            "error": None
        }
        return self
    
    def with_content(self, content: str):
        """Set response content"""
        self._response["content"] = content
        return self
    
    def with_metadata(self, key: str, value: Any):
        """Add metadata"""
        self._response["metadata"][key] = value
        return self
    
    def with_error(self, error: str):
        """Set error information"""
        self._response["status"] = "error"
        self._response["error"] = error
        return self
    
    def build(self) -> Response:
        """Build the response object"""
        response = Response(**self._response)
        self.reset()
        return response
```

### Benefits
- **Complex Object Creation**: Handle complex object construction
- **Immutability**: Objects are immutable once built
- **Validation**: Validate object state during construction
- **Fluent Interface**: Chain method calls for readability

## 7. Chain of Responsibility Pattern

### Purpose
The Chain of Responsibility pattern passes requests along a chain of handlers until one of them handles the request.

### Implementation

#### Plugin Chain
```python
class PluginChain:
    """Chain of responsibility for plugin execution"""
    
    def __init__(self):
        self.handlers: List[Plugin] = []
    
    def add_handler(self, plugin: Plugin):
        """Add a plugin to the chain"""
        self.handlers.append(plugin)
    
    async def process(self, context: Context) -> Context:
        """Process context through the chain"""
        current_context = context
        
        for handler in self.handlers:
            if handler.enabled and handler.can_handle(current_context):
                try:
                    current_context = await handler.process(current_context)
                except Exception as e:
                    logger.error(f"Error in plugin {handler.name}: {e}")
                    # Continue with next handler
        
        return current_context

class Plugin(ABC):
    """Abstract plugin interface"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
    
    @abstractmethod
    async def process(self, context: Context) -> Context:
        pass
    
    def can_handle(self, context: Context) -> bool:
        """Check if plugin can handle the context"""
        return True
```

#### Error Handling Chain
```python
class ErrorHandler(ABC):
    """Abstract error handler"""
    
    def __init__(self):
        self.next_handler: Optional[ErrorHandler] = None
    
    def set_next(self, handler: 'ErrorHandler') -> 'ErrorHandler':
        """Set the next handler in the chain"""
        self.next_handler = handler
        return handler
    
    @abstractmethod
    async def handle(self, error: Exception, context: Context) -> Optional[Response]:
        pass

class TransportErrorHandler(ErrorHandler):
    """Handle transport-related errors"""
    
    async def handle(self, error: Exception, context: Context) -> Optional[Response]:
        if isinstance(error, MCPTransportError):
            # Handle transport error
            return ResponseBuilder().with_error(f"Transport error: {error}").build()
        
        if self.next_handler:
            return await self.next_handler.handle(error, context)
        return None

class LLMErrorHandler(ErrorHandler):
    """Handle LLM-related errors"""
    
    async def handle(self, error: Exception, context: Context) -> Optional[Response]:
        if isinstance(error, LLMError):
            # Handle LLM error
            return ResponseBuilder().with_error(f"LLM error: {error}").build()
        
        if self.next_handler:
            return await self.next_handler.handle(error, context)
        return None
```

### Benefits
- **Flexibility**: Easy to add/remove handlers
- **Single Responsibility**: Each handler has one responsibility
- **Extensibility**: New handlers can be added without modifying existing code
- **Error Handling**: Graceful error handling and recovery

## 8. Template Method Pattern

### Purpose
The Template Method pattern defines the skeleton of an algorithm in a method, deferring some steps to subclasses.

### Implementation

#### Transport Template
```python
class MCPTransport(ABC):
    """Template for MCP transport implementations"""
    
    async def process_request(self, request: MCPRequest) -> MCPResponse:
        """Template method for processing requests"""
        try:
            # Hook: Pre-processing
            await self.before_request(request)
            
            # Core processing
            if not await self.is_connected():
                await self.connect()
            
            response = await self.send_request(request)
            
            # Hook: Post-processing
            await self.after_request(request, response)
            
            return response
            
        except Exception as e:
            # Hook: Error handling
            await self.on_error(request, e)
            raise
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the MCP server"""
        pass
    
    @abstractmethod
    async def send_request(self, request: MCPRequest) -> MCPResponse:
        """Send request to the server"""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """Check connection status"""
        pass
    
    # Hook methods (optional overrides)
    async def before_request(self, request: MCPRequest):
        """Called before sending request"""
        pass
    
    async def after_request(self, request: MCPRequest, response: MCPResponse):
        """Called after receiving response"""
        pass
    
    async def on_error(self, request: MCPRequest, error: Exception):
        """Called when an error occurs"""
        pass
```

### Benefits
- **Code Reuse**: Common algorithm structure is reused
- **Flexibility**: Subclasses can override specific steps
- **Consistency**: Ensures consistent behavior across implementations
- **Maintainability**: Changes to algorithm structure are centralized

## Summary

These design patterns work together to create a flexible, extensible, and maintainable system:

1. **Factory Pattern**: Creates objects based on configuration
2. **Strategy Pattern**: Provides interchangeable algorithms
3. **Observer Pattern**: Enables loose coupling through events
4. **Command Pattern**: Encapsulates requests as objects
5. **Singleton Pattern**: Manages global state and resources
6. **Builder Pattern**: Constructs complex objects step by step
7. **Chain of Responsibility**: Handles requests through a chain of handlers
8. **Template Method**: Defines algorithm skeletons with customizable steps

The combination of these patterns creates a system that is:
- **Extensible**: Easy to add new features
- **Maintainable**: Clear separation of concerns
- **Testable**: Each component can be tested independently
- **Scalable**: Can handle growth and change
- **Reliable**: Robust error handling and recovery 