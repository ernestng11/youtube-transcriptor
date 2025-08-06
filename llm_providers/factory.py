from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from typing import Dict, Optional, List

class LLMProviderFactory:
    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._registered_providers = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider
        }
    
    def get_provider(self, provider_name: str) -> BaseLLMProvider:
        """Get or create LLM provider instance with API key validation"""
        if provider_name not in self._providers:
            if provider_name not in self._registered_providers:
                available = ", ".join(self._registered_providers.keys())
                raise ValueError(f"Unknown provider: {provider_name}. Available providers: {available}")
            
            # Create provider instance
            provider = self._registered_providers[provider_name]()
            
            # Validate API key is available
            if not provider.validate_api_key():
                raise ValueError(
                    f"API key not found for {provider_name}. "
                    f"Please set the appropriate environment variable: "
                    f"{self._get_env_var_name(provider_name)}"
                )
            
            self._providers[provider_name] = provider
            print(f"✅ Initialized {provider_name} provider")
        
        return self._providers[provider_name]
    
    def _get_env_var_name(self, provider_name: str) -> str:
        """Get environment variable name for provider"""
        env_vars = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY"
        }
        return env_vars.get(provider_name, f"{provider_name.upper()}_API_KEY")
    
    def register_provider(self, name: str, provider_class: type):
        """Register a new provider class"""
        if not issubclass(provider_class, BaseLLMProvider):
            raise ValueError(f"Provider class must inherit from BaseLLMProvider")
        
        self._registered_providers[name] = provider_class
        print(f"✅ Registered new provider: {name}")
    
    def list_providers(self) -> List[str]:
        """List all available providers"""
        return list(self._registered_providers.keys())
    
    def list_active_providers(self) -> List[str]:
        """List providers that are currently initialized"""
        return list(self._providers.keys())
    
    def validate_all_providers(self) -> Dict[str, bool]:
        """Check which providers have valid API keys"""
        validation_status = {}
        
        for provider_name, provider_class in self._registered_providers.items():
            try:
                provider = provider_class()
                validation_status[provider_name] = provider.validate_api_key()
            except Exception as e:
                validation_status[provider_name] = False
        
        return validation_status
    
    def get_provider_info(self, provider_name: str) -> Dict[str, any]:
        """Get detailed information about a provider"""
        if provider_name not in self._registered_providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        provider_class = self._registered_providers[provider_name]
        provider = provider_class()
        
        return {
            "name": provider_name,
            "class": provider_class.__name__,
            "api_key_available": provider.validate_api_key(),
            "env_var": self._get_env_var_name(provider_name),
            "default_model": provider.get_default_model(),
            "available_models": provider.get_available_models() if hasattr(provider, 'get_available_models') else []
        } 