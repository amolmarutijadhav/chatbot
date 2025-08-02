"""Manager for LLM providers."""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from .llm_provider import LLMProvider
from .llm_factory import LLMFactory
from core.models import Message, Context
from utils.logger import LoggerMixin
from utils.event_bus import publish_event


class LLMManager(LoggerMixin):
    """Manager for LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize LLM manager."""
        self.config = config
        self.providers: Dict[str, LLMProvider] = {}
        self.default_provider = config.get("default_provider", "openai")
        self.fallback_providers = config.get("fallback_providers", [])
        self.load_balancing = config.get("load_balancing", "round_robin")
        self.health_check_interval = config.get("health_check_interval", 300)
        self.health_check_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the LLM manager."""
        try:
            # Initialize providers from config
            providers_config = self.config.get("providers", {})
            for provider_name, provider_config in providers_config.items():
                await self.add_provider(provider_name, provider_config)
            
            # Start health check task
            if self.health_check_interval > 0:
                self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            self.logger.info(f"LLM Manager started with {len(self.providers)} providers")
            
            # Publish event
            publish_event("llm_manager_started", {
                "providers_count": len(self.providers),
                "default_provider": self.default_provider,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Failed to start LLM Manager: {e}")
            raise
    
    async def stop(self):
        """Stop the LLM manager."""
        try:
            # Stop health check task
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
                self.health_check_task = None
            
            # Remove all providers (this will disconnect them)
            provider_names = list(self.providers.keys())
            for provider_name in provider_names:
                await self.remove_provider(provider_name)
            
            self.logger.info("LLM Manager stopped")
            
            # Publish event
            publish_event("llm_manager_stopped", {
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error stopping LLM Manager: {e}")
    
    async def add_provider(self, name: str, config: Dict[str, Any]) -> bool:
        """Add a new LLM provider."""
        try:
            # Validate config
            if not LLMFactory.validate_provider_config(name, config):
                return False
            
            # Create provider
            provider = LLMFactory.create_provider(name, config)
            
            # Connect provider
            if await provider.connect():
                self.providers[name] = provider
                self.logger.info(f"Added LLM provider: {name}")
                
                # Publish event
                publish_event("llm_provider_added", {
                    "provider": name,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return True
            else:
                self.logger.error(f"Failed to connect provider: {name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding provider '{name}': {e}")
            return False
    
    async def remove_provider(self, name: str) -> bool:
        """Remove an LLM provider."""
        if name not in self.providers:
            return False
        
        try:
            provider = self.providers[name]
            await provider.disconnect()
            del self.providers[name]
            
            self.logger.info(f"Removed LLM provider: {name}")
            
            # Publish event
            publish_event("llm_provider_removed", {
                "provider": name,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing provider '{name}': {e}")
            return False
    
    async def generate_response(
        self, 
        messages: List[Message], 
        context: Optional[Context] = None,
        provider_name: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate response using the best available provider."""
        if not self.providers:
            raise RuntimeError("No LLM providers available")
        
        # Determine which provider to use
        if provider_name:
            if provider_name not in self.providers:
                raise ValueError(f"Provider '{provider_name}' not found")
            providers_to_try = [provider_name]
        else:
            providers_to_try = self._get_provider_priority_list()
        
        # Try providers in order
        last_error = None
        for provider_name in providers_to_try:
            try:
                provider = self.providers[provider_name]
                
                # Check if provider is connected
                if not provider.is_connected:
                    if not await provider.connect():
                        continue
                
                # Generate response
                response = await provider.generate_response(messages, context, **kwargs)
                
                self.logger.info(f"Generated response using provider: {provider_name}")
                return response
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"Provider '{provider_name}' failed: {e}")
                
                # Try to reconnect provider
                try:
                    await provider.disconnect()
                    await provider.connect()
                except Exception:
                    pass
                
                continue
        
        # All providers failed
        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")
    
    def _get_provider_priority_list(self) -> List[str]:
        """Get list of providers in priority order."""
        providers = []
        
        # Add default provider first
        if self.default_provider in self.providers:
            providers.append(self.default_provider)
        
        # Add fallback providers
        for fallback in self.fallback_providers:
            if fallback in self.providers and fallback not in providers:
                providers.append(fallback)
        
        # Add any remaining providers
        for provider_name in self.providers:
            if provider_name not in providers:
                providers.append(provider_name)
        
        return providers
    
    async def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics for all providers."""
        stats = {
            "total_providers": len(self.providers),
            "connected_providers": 0,
            "providers": {}
        }
        
        for name, provider in self.providers.items():
            provider_stats = provider.get_stats()
            stats["providers"][name] = provider_stats
            
            if provider.is_connected:
                stats["connected_providers"] += 1
        
        return stats
    
    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on all providers."""
        health_status = {}
        
        for name, provider in self.providers.items():
            try:
                is_healthy = await provider.validate_connection()
                health_status[name] = is_healthy
                
                if not is_healthy and provider.is_connected:
                    self.logger.warning(f"Provider '{name}' health check failed")
                    await provider.disconnect()
                    await provider.connect()
                    
            except Exception as e:
                self.logger.error(f"Health check failed for provider '{name}': {e}")
                health_status[name] = False
        
        return health_status
    
    async def _health_check_loop(self):
        """Background task for periodic health checks."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self.health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
    
    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """Get a specific provider by name."""
        return self.providers.get(name)
    
    def list_providers(self) -> List[str]:
        """Get list of all provider names."""
        return list(self.providers.keys())
    
    def is_provider_available(self, name: str) -> bool:
        """Check if a provider is available and connected."""
        provider = self.providers.get(name)
        return provider is not None and provider.is_connected
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop() 