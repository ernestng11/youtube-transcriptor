from .base import BaseLLMProvider, LLMConfig
from typing import Dict, List, Optional
import os
try:
    import openai
except ImportError:
    openai = None
import json

class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__()
        self.client: Optional[openai.AsyncOpenAI] = None
        self._api_key: Optional[str] = None
    
    def get_api_key(self) -> Optional[str]:
        """Get OpenAI API key from environment variables"""
        if self._api_key is None:
            self._api_key = os.getenv("OPENAI_API_KEY")
        return self._api_key
    
    def get_default_model(self) -> str:
        """Get default OpenAI model"""
        return "gpt-4o-mini"
    
    def _initialize_client(self):
        """Initialize OpenAI client with API key"""
        if self.client is None:
            if openai is None:
                raise ImportError("OpenAI package not installed. Please install with: pip install openai")
            
            api_key = self.get_api_key()
            if api_key is None:
                raise ValueError(
                    "OpenAI API key not found. Please set OPENAI_API_KEY environment variable."
                )
            
            self.client = openai.AsyncOpenAI(api_key=api_key)
    
    async def generate_response(self, messages: List[Dict], config: LLMConfig) -> str:
        """Generate response using OpenAI API"""
        self._initialize_client()
        
        try:
            response = await self.client.chat.completions.create(
                model=config.model_name or self.get_default_model(),
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                **(config.additional_params or {})
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def tool_call(self, messages: List[Dict], tools: List[Dict], config: LLMConfig) -> Dict:
        """Perform tool calling with OpenAI API"""
        self._initialize_client()
        
        try:
            response = await self.client.chat.completions.create(
                model=config.model_name or self.get_default_model(),
                messages=messages,
                tools=tools,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                **(config.additional_params or {})
            )
            
            return {
                "message": response.choices[0].message,
                "tool_calls": response.choices[0].message.tool_calls if hasattr(response.choices[0].message, 'tool_calls') else None
            }
        except Exception as e:
            raise Exception(f"OpenAI tool call error: {str(e)}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models"""
        return [
            "gpt-4o",
            "gpt-4o-mini"
        ] 