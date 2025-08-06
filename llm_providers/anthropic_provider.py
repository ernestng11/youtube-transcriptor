from .base import BaseLLMProvider, LLMConfig
from typing import Dict, List, Optional
import os
try:
    import anthropic
except ImportError:
    anthropic = None
import json

class AnthropicProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__()
        self.client: Optional[anthropic.AsyncAnthropic] = None
        self._api_key: Optional[str] = None
    
    def get_api_key(self) -> Optional[str]:
        """Get Anthropic API key from environment variables"""
        if self._api_key is None:
            self._api_key = os.getenv("ANTHROPIC_API_KEY")
        return self._api_key
    
    def get_default_model(self) -> str:
        """Get default Anthropic model"""
        return "claude-3-haiku-20240307"
    
    def _initialize_client(self):
        """Initialize Anthropic client with API key"""
        if self.client is None:
            if anthropic is None:
                raise ImportError("Anthropic package not installed. Please install with: pip install anthropic")
            
            api_key = self.get_api_key()
            if api_key is None:
                raise ValueError(
                    "Anthropic API key not found. Please set ANTHROPIC_API_KEY environment variable."
                )
            
            self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def generate_response(self, messages: List[Dict], config: LLMConfig) -> str:
        """Generate response using Anthropic API"""
        self._initialize_client()
        
        try:
            # Convert OpenAI format to Anthropic format
            anthropic_messages = self._convert_messages(messages)
            
            response = await self.client.messages.create(
                model=config.model_name or self.get_default_model(),
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                messages=anthropic_messages,
                **(config.additional_params or {})
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    async def tool_call(self, messages: List[Dict], tools: List[Dict], config: LLMConfig) -> Dict:
        """Perform tool calling with Anthropic API"""
        self._initialize_client()
        
        try:
            # Convert tools to Anthropic format
            anthropic_tools = self._convert_tools(tools)
            anthropic_messages = self._convert_messages(messages)
            
            response = await self.client.messages.create(
                model=config.model_name or self.get_default_model(),
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                messages=anthropic_messages,
                tools=anthropic_tools,
                **(config.additional_params or {})
            )
            
            return {
                "message": response,
                "tool_calls": [block for block in response.content if hasattr(block, 'type') and block.type == 'tool_use']
            }
        except Exception as e:
            raise Exception(f"Anthropic tool call error: {str(e)}")
    
    def _convert_messages(self, messages: List[Dict]) -> List[Dict]:
        """Convert OpenAI message format to Anthropic format"""
        anthropic_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                # Anthropic handles system messages differently
                continue
            anthropic_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        return anthropic_messages
    
    def _convert_tools(self, tools: List[Dict]) -> List[Dict]:
        """Convert OpenAI tool format to Anthropic format"""
        anthropic_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                anthropic_tools.append({
                    "name": tool["function"]["name"],
                    "description": tool["function"]["description"],
                    "input_schema": tool["function"]["parameters"]
                })
        return anthropic_tools
    
    def get_available_models(self) -> List[str]:
        """Get list of available Anthropic models"""
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229", 
            "claude-3-haiku-20240307"
        ] 