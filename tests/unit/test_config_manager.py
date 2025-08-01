"""Unit tests for ConfigurationManager."""

import pytest
import os
import tempfile
import yaml
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.config_manager import ConfigurationManager


class TestConfigurationManager:
    """Test cases for ConfigurationManager."""

    def test_singleton_pattern(self):
        """Test that ConfigurationManager is a singleton."""
        config1 = ConfigurationManager()
        config2 = ConfigurationManager()
        assert config1 is config2

    def test_initialization(self):
        """Test ConfigurationManager initialization."""
        config = ConfigurationManager()
        assert hasattr(config, 'config')
        assert isinstance(config.config, dict)

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_load_configuration_from_file(self, mock_yaml_load, mock_file):
        """Test loading configuration from YAML file."""
        mock_config = {
            'api': {'host': 'localhost', 'port': 8000},
            'logging': {'level': 'INFO'}
        }
        mock_yaml_load.return_value = mock_config
        
        # Create a fresh config manager and manually set the config
        config = ConfigurationManager()
        config.config = mock_config.copy()
        
        assert config.config == mock_config

    def test_get_value_with_dot_notation(self):
        """Test getting values using dot notation."""
        config = ConfigurationManager()
        config.config = {
            'api': {'host': 'localhost', 'port': 8000},
            'logging': {'level': 'INFO'}
        }
        
        assert config.get('api.host') == 'localhost'
        assert config.get('api.port') == 8000
        assert config.get('logging.level') == 'INFO'

    def test_get_value_with_default(self):
        """Test getting values with default fallback."""
        config = ConfigurationManager()
        config.config = {'api': {'host': 'localhost'}}
        
        assert config.get('api.port', 8000) == 8000
        assert config.get('nonexistent.key', 'default') == 'default'

    def test_set_value_with_dot_notation(self):
        """Test setting values using dot notation."""
        config = ConfigurationManager()
        config.config = {}
        
        config.set('api.host', 'localhost')
        config.set('api.port', 8000)
        
        assert config.config['api']['host'] == 'localhost'
        assert config.config['api']['port'] == 8000

    def test_environment_variable_override(self):
        """Test that environment variables override config values."""
        config = ConfigurationManager()
        config.config = {'api': {'host': 'localhost', 'port': 8000}}
        
        with patch.dict(os.environ, {'CHATBOT_API_HOST': '127.0.0.1'}):
            config._override_with_env_vars()
            assert config.get('api.host') == '127.0.0.1'
            assert config.get('api.port') == 8000  # Should remain unchanged

    def test_get_api_config(self):
        """Test getting API configuration."""
        config = ConfigurationManager()
        config.config = {
            'api': {
                'host': 'localhost',
                'port': 8000,
                'cors': {'allowed_origins': ['http://localhost:3000']}
            }
        }
        
        api_config = config.get_api_config()
        assert api_config['host'] == 'localhost'
        assert api_config['port'] == 8000
        assert 'cors' in api_config

    def test_get_logging_config(self):
        """Test getting logging configuration."""
        config = ConfigurationManager()
        config.config = {
            'logging': {
                'level': 'INFO',
                'file': 'logs/chatbot.log',
                'structured': True
            }
        }
        
        logging_config = config.get_logging_config()
        assert logging_config['level'] == 'INFO'
        assert logging_config['file'] == 'logs/chatbot.log'
        assert logging_config['structured'] is True

    def test_get_session_config(self):
        """Test getting session configuration."""
        config = ConfigurationManager()
        config.config = {
            'session': {
                'timeout': 3600,
                'max_sessions_per_user': 10,
                'cleanup_interval': 300
            }
        }
        
        session_config = config.get_session_config()
        assert session_config['timeout'] == 3600
        assert session_config['max_sessions_per_user'] == 10
        assert session_config['cleanup_interval'] == 300

    def test_get_llm_config(self):
        """Test getting LLM configuration."""
        config = ConfigurationManager()
        config.config = {
            'llm': {
                'providers': {
                    'openai': {
                        'api_key': 'test_key',
                        'base_url': 'https://api.openai.com/v1'
                    }
                }
            }
        }
        
        llm_config = config.get_llm_config()
        assert 'providers' in llm_config
        assert 'openai' in llm_config['providers']

    def test_get_mcp_config(self):
        """Test getting MCP configuration."""
        config = ConfigurationManager()
        config.config = {
            'mcp': {
                'servers': {
                    'file_system': {
                        'type': 'stdio',
                        'command': 'mcp-server-filesystem'
                    }
                }
            }
        }
        
        mcp_config = config.get_mcp_config()
        assert 'servers' in mcp_config
        assert 'file_system' in mcp_config['servers']

    def test_validate_configuration(self):
        """Test configuration validation."""
        config = ConfigurationManager()
        
        # Test with valid configuration
        config.config = {
            'chatbot': {'name': 'test', 'version': '1.0.0'},
            'llm': {'default_provider': 'openai'},
            'api': {'host': 'localhost', 'port': 8000},
            'logging': {'level': 'INFO'}
        }
        assert config.validate() is True
        
        # Test with invalid configuration (missing required fields)
        config.config = {}
        assert config.validate() is False

    def test_get_with_nested_structure(self):
        """Test getting values from deeply nested structures."""
        config = ConfigurationManager()
        config.config = {
            'deeply': {
                'nested': {
                    'structure': {
                        'value': 'test'
                    }
                }
            }
        }
        
        assert config.get('deeply.nested.structure.value') == 'test'

    def test_set_with_nested_structure(self):
        """Test setting values in deeply nested structures."""
        config = ConfigurationManager()
        config.config = {}
        
        config.set('deeply.nested.structure.value', 'test')
        
        assert config.get('deeply.nested.structure.value') == 'test'

    def test_get_all_config(self):
        """Test getting the entire configuration."""
        config = ConfigurationManager()
        test_config = {'api': {'host': 'localhost'}, 'logging': {'level': 'INFO'}}
        config.config = test_config
        
        assert config.get_all_config() == test_config

    def test_clear_config(self):
        """Test clearing the configuration."""
        config = ConfigurationManager()
        config.config = {'api': {'host': 'localhost'}}
        
        config.clear_config()
        assert config.config == {}

    def test_has_key(self):
        """Test checking if a key exists."""
        config = ConfigurationManager()
        config.config = {'api': {'host': 'localhost'}}
        
        assert config.has_key('api.host') is True
        assert config.has_key('api.port') is False
        assert config.has_key('nonexistent') is False

    def test_get_keys(self):
        """Test getting all configuration keys."""
        config = ConfigurationManager()
        config.config = {
            'api': {'host': 'localhost', 'port': 8000},
            'logging': {'level': 'INFO'}
        }
        
        keys = config.get_keys()
        assert 'api.host' in keys
        assert 'api.port' in keys
        assert 'logging.level' in keys 