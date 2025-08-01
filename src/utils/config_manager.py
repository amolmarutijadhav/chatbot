"""Configuration management for the chatbot system."""

import os
import threading
from typing import Any, Dict, Optional, List
import yaml
from pathlib import Path


class ConfigurationManager:
    """Singleton for managing system configuration."""
    
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
            self.config: Dict[str, Any] = {}
            self.load_configuration()
            self.initialized = True
    
    def load_configuration(self):
        """Load configuration from files and environment."""
        # Load from YAML files
        config_files = [
            "config/chatbot_config.yaml",
            "config/mcp_servers.yaml",
            "config/plugins.yaml"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        self.config.update(file_config)
        
        # Override with environment variables
        self._load_from_environment()
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        # LLM API keys
        if os.getenv("OPENAI_API_KEY"):
            self.config.setdefault("llm", {}).setdefault("providers", {})
            self.config["llm"]["providers"].setdefault("openai", {})
            self.config["llm"]["providers"]["openai"]["api_key"] = os.getenv("OPENAI_API_KEY")
        
        if os.getenv("ANTHROPIC_API_KEY"):
            self.config.setdefault("llm", {}).setdefault("providers", {})
            self.config["llm"]["providers"].setdefault("anthropic", {})
            self.config["llm"]["providers"]["anthropic"]["api_key"] = os.getenv("ANTHROPIC_API_KEY")
        
        # MCP API keys
        if os.getenv("MCP_API_KEY"):
            self.config.setdefault("mcp", {}).setdefault("api_key", os.getenv("MCP_API_KEY"))
        
        if os.getenv("DB_API_KEY"):
            self.config.setdefault("mcp", {}).setdefault("db_api_key", os.getenv("DB_API_KEY"))
        
        # JWT secret
        if os.getenv("JWT_SECRET_KEY"):
            self.config.setdefault("api", {}).setdefault("auth", {})
            self.config["api"]["auth"]["secret_key"] = os.getenv("JWT_SECRET_KEY")
        
        # Environment-specific settings
        if os.getenv("CHATBOT_ENVIRONMENT"):
            self.config.setdefault("chatbot", {})["environment"] = os.getenv("CHATBOT_ENVIRONMENT")
        
        if os.getenv("CHATBOT_DEBUG"):
            self.config.setdefault("chatbot", {})["debug"] = os.getenv("CHATBOT_DEBUG").lower() == "true"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def get_llm_config(self, provider: str = None) -> Dict[str, Any]:
        """Get LLM provider configuration."""
        if provider:
            return self.get(f"llm.providers.{provider}", {})
        return self.get("llm", {})
    
    def _override_with_env_vars(self):
        """Override configuration with environment variables."""
        for key, value in os.environ.items():
            if key.startswith('CHATBOT_'):
                # Convert CHATBOT_API_HOST to api.host
                config_key = key[8:].lower().replace('_', '.')
                self.set(config_key, value)
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get the entire configuration."""
        return self.config.copy()
    
    def clear_config(self):
        """Clear the configuration."""
        self.config.clear()
    
    def has_key(self, key: str) -> bool:
        """Check if a key exists in configuration."""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return True
        except (KeyError, TypeError):
            return False
    
    def get_keys(self) -> List[str]:
        """Get all configuration keys in dot notation."""
        def _flatten_dict(d, prefix=''):
            keys = []
            for k, v in d.items():
                new_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    keys.extend(_flatten_dict(v, new_key))
                else:
                    keys.append(new_key)
            return keys
        
        return _flatten_dict(self.config)
    
    def get_mcp_config(self) -> Dict[str, Any]:
        """Get MCP configuration."""
        return self.get("mcp", {})
    
    def get_plugin_config(self) -> Dict[str, Any]:
        """Get plugin configuration."""
        return self.get("plugins", {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration."""
        return self.get("api", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get("logging", {})
    
    def get_session_config(self) -> Dict[str, Any]:
        """Get session configuration."""
        return self.get("session", {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration."""
        return self.get("performance", {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return self.get("security", {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return self.get("monitoring", {})
    
    def get_error_handling_config(self) -> Dict[str, Any]:
        """Get error handling configuration."""
        return self.get("error_handling", {})
    
    def get_development_config(self) -> Dict[str, Any]:
        """Get development configuration."""
        return self.get("development", {})
    
    def reload(self):
        """Reload configuration from files and environment."""
        self.config.clear()
        self.load_configuration()
    
    def validate(self) -> bool:
        """Validate configuration."""
        required_keys = [
            "chatbot.name",
            "chatbot.version",
            "llm.default_provider"
        ]
        
        for key in required_keys:
            if not self.get(key):
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return self.config.copy()
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return f"ConfigurationManager(config={self.config})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"ConfigurationManager(config_keys={list(self.config.keys())})" 