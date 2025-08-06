# 🧠 LLM Providers System

A modular, extensible system for integrating multiple Large Language Model (LLM) providers with a unified interface. This system provides seamless switching between OpenAI, Anthropic, and custom LLM providers while maintaining consistent API patterns.

## 🏗️ Architecture Overview

```
src/llm_providers/
├── __init__.py           # Public API exports
├── base.py              # Abstract base classes and configuration
├── factory.py           # Provider factory and management
├── openai_provider.py   # OpenAI API implementation
├── anthropic_provider.py # Anthropic API implementation
└── README.md           # This documentation
```

### Core Components

- **`BaseLLMProvider`**: Abstract base class defining the provider interface
- **`LLMConfig`**: Configuration dataclass for model settings
- **`LLMProviderFactory`**: Factory pattern for provider management
- **Provider Implementations**: Concrete implementations for different APIs

## 🚀 Quick Start

### 1. Installation

Ensure you have the required dependencies installed:

```bash
# For OpenAI
pip install openai

# For Anthropic  
pip install anthropic

# Or install both
pip install openai anthropic
```

### 2. Environment Setup

Set your API keys as environment variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 3. Basic Usage

```python
from src.llm_providers import LLMProviderFactory, LLMConfig

# Initialize factory
factory = LLMProviderFactory()

# Get provider (automatically validates API key)
provider = factory.get_provider("openai")

# Create configuration
config = LLMConfig(
    model_name="gpt-4o-mini",
    temperature=0.7,
    max_tokens=1000
)

# Generate response
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello! How are you?"}
]

response = await provider.generate_response(messages, config)
print(response)
```

## 📚 API Reference

### LLMConfig

Configuration dataclass for model parameters.

```python
@dataclass
class LLMConfig:
    model_name: str                                    # Model to use
    temperature: float = 0.7                          # Randomness (0.0-1.0)
    max_tokens: int = 2048                            # Maximum response length
    additional_params: Dict[str, Any] = field(default_factory=dict)  # Provider-specific params
```

### BaseLLMProvider

Abstract base class that all providers must implement.

#### Methods

- **`generate_response(messages, config)`** → `str`
  - Generate text response from the LLM
  - `messages`: List of message dictionaries
  - `config`: LLMConfig instance
  - Returns: Generated text response

- **`tool_call(messages, tools, config)`** → `Dict`
  - Perform function calling with the LLM
  - `tools`: List of tool/function definitions
  - Returns: Response with tool call information

- **`get_api_key()`** → `Optional[str]`
  - Retrieve API key from environment variables

- **`get_default_model()`** → `str`
  - Get the default model name for this provider

- **`validate_api_key()`** → `bool`
  - Check if API key is available and valid

### LLMProviderFactory

Factory class for managing provider instances.

#### Methods

- **`get_provider(provider_name)`** → `BaseLLMProvider`
  - Get or create provider instance
  - Validates API key automatically
  - Supported providers: `"openai"`, `"anthropic"`

- **`list_providers()`** → `List[str]`
  - List all available provider names

- **`list_active_providers()`** → `List[str]`
  - List currently initialized providers

- **`validate_all_providers()`** → `Dict[str, bool]`
  - Check API key status for all providers

- **`get_provider_info(provider_name)`** → `Dict`
  - Get detailed provider information

- **`register_provider(name, provider_class)`**
  - Register custom provider implementation

## 🔧 Provider Details

### OpenAI Provider

**Environment Variable**: `OPENAI_API_KEY`

**Available Models**:
- `gpt-4o` - Latest GPT-4 Omni model
- `gpt-4o-mini` - Faster, cost-effective version (default)

**Features**:
- Chat completions
- Function calling
- Streaming support (via additional_params)

### Anthropic Provider

**Environment Variable**: `ANTHROPIC_API_KEY`

**Available Models**:
- `claude-3-opus-20240229` - Most capable model
- `claude-3-sonnet-20240229` - Balanced performance
- `claude-3-haiku-20240307` - Fast and cost-effective (default)

**Features**:
- Message format conversion (OpenAI → Anthropic)
- Tool calling with format translation
- System message handling

## 🎯 Advanced Usage

### Multi-Provider Setup

```python
factory = LLMProviderFactory()

# Check which providers are available
status = factory.validate_all_providers()
print(f"Available providers: {status}")
# Output: {'openai': True, 'anthropic': False}

# Use available provider
for provider_name, available in status.items():
    if available:
        provider = factory.get_provider(provider_name)
        break
```

### Custom Configuration

```python
# Custom configuration with provider-specific parameters
config = LLMConfig(
    model_name="gpt-4o",
    temperature=0.3,
    max_tokens=500,
    additional_params={
        "top_p": 0.9,
        "frequency_penalty": 0.1,
        "stream": False
    }
)
```

### Function Calling

```python
# Define tools/functions
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather information for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"}
                },
                "required": ["location"]
            }
        }
    }
]

# Call with tools
result = await provider.tool_call(messages, tools, config)
if result["tool_calls"]:
    # Process tool calls
    for tool_call in result["tool_calls"]:
        print(f"Function: {tool_call.function.name}")
        print(f"Arguments: {tool_call.function.arguments}")
```

### Provider Information

```python
# Get detailed provider info
info = factory.get_provider_info("openai")
print(f"""
Provider: {info['name']}
Class: {info['class']}
API Key Available: {info['api_key_available']}
Environment Variable: {info['env_var']}
Default Model: {info['default_model']}
Available Models: {info['available_models']}
""")
```

## 🔌 Creating Custom Providers

### 1. Implement BaseLLMProvider

```python
from src.llm_providers.base import BaseLLMProvider, LLMConfig
from typing import Dict, List, Optional

class CustomProvider(BaseLLMProvider):
    def get_api_key(self) -> Optional[str]:
        return os.getenv("CUSTOM_API_KEY")
    
    def get_default_model(self) -> str:
        return "custom-model-v1"
    
    async def generate_response(self, messages: List[Dict], config: LLMConfig) -> str:
        # Implement your custom API call logic
        pass
    
    async def tool_call(self, messages: List[Dict], tools: List[Dict], config: LLMConfig) -> Dict:
        # Implement tool calling logic
        pass
    
    def get_available_models(self) -> List[str]:
        return ["custom-model-v1", "custom-model-v2"]
```

### 2. Register Your Provider

```python
factory = LLMProviderFactory()
factory.register_provider("custom", CustomProvider)

# Now you can use it
provider = factory.get_provider("custom")
```

## 🐛 Troubleshooting

### Common Issues

**1. API Key Not Found**
```
ValueError: API key not found for openai. Please set the appropriate environment variable: OPENAI_API_KEY
```
**Solution**: Set the required environment variable with your API key.

**2. Import Error**
```
ImportError: OpenAI package not installed. Please install with: pip install openai
```
**Solution**: Install the required package: `pip install openai` or `pip install anthropic`

**3. Model Not Available**
```
Exception: OpenAI API error: The model 'gpt-5' does not exist
```
**Solution**: Use a valid model name. Check `provider.get_available_models()` for options.

### Debugging Tips

```python
# Check provider status
factory = LLMProviderFactory()
status = factory.validate_all_providers()
print("Provider Status:", status)

# Get provider details
for provider_name in factory.list_providers():
    try:
        info = factory.get_provider_info(provider_name)
        print(f"{provider_name}: {info}")
    except Exception as e:
        print(f"{provider_name}: Error - {e}")

# Test basic functionality
try:
    provider = factory.get_provider("openai")
    config = LLMConfig(model_name="gpt-4o-mini", max_tokens=50)
    response = await provider.generate_response([
        {"role": "user", "content": "Say hello"}
    ], config)
    print("Test successful:", response)
except Exception as e:
    print("Test failed:", e)
```

## 📋 Best Practices

### 1. Configuration Management
- Use environment variables for API keys
- Create reusable LLMConfig instances for common settings
- Set appropriate timeouts and token limits

### 2. Error Handling
```python
try:
    provider = factory.get_provider("openai")
    response = await provider.generate_response(messages, config)
except ValueError as e:
    # Handle API key or configuration errors
    print(f"Configuration error: {e}")
except Exception as e:
    # Handle API or network errors
    print(f"API error: {e}")
```

### 3. Performance Optimization
- Reuse provider instances (factory handles this automatically)
- Use appropriate model sizes for your use case
- Set reasonable token limits to control costs

### 4. Testing
- Always validate API keys before deployment
- Test with minimal token limits during development
- Use mock providers for unit testing

## 🤝 Contributing

To add support for a new LLM provider:

1. Create a new provider file (e.g., `cohere_provider.py`)
2. Implement the `BaseLLMProvider` interface
3. Add import and registration in `factory.py`
4. Update `__init__.py` exports
5. Add tests and documentation
6. Update this README

## 📄 License

This LLM provider system is part of the mantlebrain project. See the main project license for details.
