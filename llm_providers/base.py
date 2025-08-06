from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import os

@dataclass
class LLMConfig:
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2048
    additional_params: Dict[str, Any] = field(default_factory=dict)

class BaseLLMProvider(ABC):
    """Base class for all LLM providers"""
    
    def __init__(self):
        self.provider_name = self.__class__.__name__.replace("Provider", "").lower()
    
    @abstractmethod
    async def generate_response(self, messages: List[Dict], config: LLMConfig) -> str:
        """Generate text response from the LLM"""
        pass
    
    @abstractmethod
    async def tool_call(self, messages: List[Dict], tools: List[Dict], config: LLMConfig) -> Dict:
        """Perform tool calling with the LLM"""
        pass
    
    @abstractmethod
    def get_api_key(self) -> Optional[str]:
        """Get the API key for this provider from environment variables"""
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Get the default model name for this provider"""
        pass
    
    def validate_api_key(self) -> bool:
        """Validate that the API key is available"""
        return self.get_api_key() is not None 