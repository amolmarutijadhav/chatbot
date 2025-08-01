# Intelligent MCP Chatbot

A highly extensible, plugin-based chatbot system with Model Context Protocol (MCP) server integration support.

## 🏗️ Architecture Overview

This system follows clean architecture principles with a modular, plugin-based design that supports multiple MCP transport protocols and LLM providers.

### Core Components

- **Chatbot Engine**: Central message processing and session management
- **MCP Integration**: Extensible transport layer for MCP server communication
- **Plugin System**: Hot-swappable functionality extensions
- **LLM Integration**: Configurable LLM provider support
- **Event System**: Event-driven architecture for system-wide communication

## 📁 Project Structure

```
chatbot/
├── docs/                           # Documentation
│   ├── architecture.md             # System architecture
│   ├── design_patterns.md          # Design patterns used
│   ├── api_reference.md            # API documentation
│   └── deployment.md               # Deployment guide
├── src/                            # Source code
│   ├── core/                       # Core chatbot engine
│   ├── mcp/                        # MCP integration layer
│   ├── llm/                        # LLM provider integration
│   ├── plugins/                    # Plugin system
│   ├── transports/                 # Transport implementations
│   ├── api/                        # REST API and WebSocket
│   └── utils/                      # Shared utilities
├── config/                         # Configuration files
├── tests/                          # Test suite
├── examples/                       # Usage examples
├── scripts/                        # Utility scripts
└── requirements.txt                # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- pip or poetry

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd chatbot

# Install dependencies
pip install -r requirements.txt

# Copy configuration template
cp config/chatbot_config.yaml.example config/chatbot_config.yaml

# Edit configuration
nano config/chatbot_config.yaml

# Run the chatbot
python -m src.main
```

### Configuration

Edit `config/chatbot_config.yaml` to configure:

- LLM providers (OpenAI, Anthropic, etc.)
- MCP servers (STDIO, HTTP)
- Plugins
- API settings

## 🔧 Key Features

### MCP Transport Support

- **STDIO**: Process-based MCP servers
- **HTTP**: RESTful MCP server communication
- **Extensible**: Easy to add new transport types

### LLM Integration

- **Multi-Provider**: Support for multiple LLM providers
- **Configurable URLs**: Full URL customization
- **Fallback Support**: Automatic fallback mechanisms

### Plugin System

- **Pre-Processing**: Context modification before processing
- **Post-Processing**: Response modification after processing
- **Event Handlers**: System event response
- **Dynamic Loading**: Runtime plugin management

## 📚 Documentation

- [Architecture Guide](docs/architecture.md)
- [Design Patterns](docs/design_patterns.md)
- [API Reference](docs/api_reference.md)
- [Deployment Guide](docs/deployment.md)

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=src
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details 