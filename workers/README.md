# 🔧 Workers - LLM Processing System

Worker class system for processing JSON data using Large Language Models (LLMs) with customizable prompts and multiple provider support.

## 🏗️ Architecture Overview

```
src/llm_providers/
├── __init__.py           # Public API exports
├── base.py              # Abstract base classes and configuration
├── factory.py           # Provider factory and management
├── openai_provider.py   # OpenAI API implementation
├── anthropic_provider.py # Anthropic API implementation

src/workers/
├── __init__.py        # Public API exports
├── llm_process.py     # Main LLMProcess worker class
```

The `LLMProcess` class provides a high-level interface for processing JSON data through LLM providers with pre-defined prompt templates and custom processing capabilities.

### Core Components

- **`LLMProcess`**: Main worker class with class methods for JSON processing
- **`ProcessingResult`**: Dataclass containing processing results and metadata
- **`PromptType`**: Enum defining different types of analysis prompts
- **Integration**: Seamless integration with `src/llm_providers/` system

## 🚀 Quick Start

### 1. Prerequisites

Ensure you have the LLM providers system set up:

```bash
# Install required dependencies
pip install openai anthropic

# Set up API keys
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 2. Basic Usage

```python
import asyncio
from src.workers import LLMProcess, PromptType

# Sample JSON data
data = {
    "user_activity": [
        {"action": "login", "timestamp": "2024-01-15T10:00:00Z"},
        {"action": "purchase", "amount": 49.99, "item": "premium_plan"}
    ],
    "metadata": {"user_id": "12345", "session": "abc123"}
}

async def main():
    # Analyze the data
    result = await LLMProcess.analyze_content(data)
    
    if result.success:
        print("Analysis Result:")
        print(result.result)
    else:
        print(f"Error: {result.error}")

asyncio.run(main())
```

## 📚 API Reference

### LLMProcess Class

The main worker class providing static methods for JSON processing.

#### Core Processing Methods

##### `analyze_content(json_data, provider_name="openai", config=None)`

Analyze JSON content for patterns, insights, and recommendations.

```python
result = await LLMProcess.analyze_content(
    json_data={"sales": [100, 150, 200], "month": "January"},
    provider_name="openai"
)
```

**Parameters:**
- `json_data`: JSON data as dict or string
- `provider_name`: LLM provider to use ("openai" or "anthropic")
- `config`: Optional LLMConfig instance

**Returns:** `ProcessingResult`

##### `classify_data(json_data, provider_name="openai", config=None)`

Classify JSON data into appropriate categories with confidence scoring.

```python
result = await LLMProcess.classify_data(
    json_data={"text": "Bitcoin price is rising!", "source": "twitter"},
    provider_name="openai"
)
```

##### `extract_insights(json_data, provider_name="openai", config=None)`

Extract key insights, entities, and relationships from JSON data.

```python
result = await LLMProcess.extract_insights(
    json_data={"news_articles": [...], "market_data": {...}},
    provider_name="anthropic"
)
```

##### `summarize_data(json_data, provider_name="openai", config=None)`

Create concise summaries of JSON data with key points and metrics.

```python
result = await LLLProcess.summarize_data(
    json_data={"quarterly_report": {...}, "metrics": {...}},
    provider_name="openai"
)
```

##### `custom_process(json_data, custom_instructions, provider_name="openai", config=None)`

Process JSON data with custom instructions for specific analysis needs.

```python
result = await LLMProcess.custom_process(
    json_data=crypto_data,
    custom_instructions="""
    Analyze cryptocurrency mentions and extract:
    1. Coin names and symbols
    2. Sentiment (bullish/bearish/neutral)
    3. Price predictions or targets
    4. Trading volume implications
    """,
    provider_name="openai"
)
```

#### Advanced Methods

##### `process_json_with_prompt(json_data, prompt_type, custom_prompt=None, ...)`

Main processing method with full customization options.

```python
result = await LLMProcess.process_json_with_prompt(
    json_data=data,
    prompt_type=PromptType.ANALYZE,
    custom_prompt="Custom analysis prompt: {json_data}",
    provider_name="anthropic",
    config=custom_config
)
```

**Parameters:**
- `json_data`: JSON data to process
- `prompt_type`: PromptType enum value
- `custom_prompt`: Custom prompt template (overrides prompt_type)
- `custom_instructions`: Instructions for CUSTOM prompt type
- `provider_name`: LLM provider name
- `config`: LLMConfig instance

##### `batch_process(json_data_list, prompt_type, provider_name="openai", config=None, max_concurrent=3)`

Process multiple JSON data items in parallel with concurrency control.

```python
batch_data = [
    {"tweet": "Bitcoin bullish trend", "sentiment": "unknown"},
    {"tweet": "Ethereum concerns rising", "sentiment": "unknown"},
    {"tweet": "DeFi protocols growing", "sentiment": "unknown"}
]

results = await LLMProcess.batch_process(
    json_data_list=batch_data,
    prompt_type=PromptType.CLASSIFY,
    provider_name="openai",
    max_concurrent=2
)

for i, result in enumerate(results):
    print(f"Item {i+1}: {'Success' if result.success else 'Failed'}")
```

#### Utility Methods

##### `get_available_providers()`

Get status of available LLM providers.

```python
providers = LLMProcess.get_available_providers()
print(providers)  # {'openai': True, 'anthropic': False}
```

##### `create_custom_config(model_name=None, temperature=0.3, max_tokens=1000, **additional_params)`

Create custom LLM configuration.

```python
config = LLMProcess.create_custom_config(
    model_name="gpt-4o",
    temperature=0.8,
    max_tokens=1500,
    top_p=0.9
)
```

### ProcessingResult

Dataclass containing processing results and metadata.

```python
@dataclass
class ProcessingResult:
    success: bool                              # Whether processing succeeded
    result: Optional[str] = None              # LLM response text
    error: Optional[str] = None               # Error message if failed
    input_data: Optional[Dict[str, Any]] = None  # Original input data
    prompt_type: Optional[str] = None         # Type of prompt used
    model_used: Optional[str] = None          # Model name used
    tokens_used: Optional[int] = None         # Tokens consumed (future)
```

### PromptType Enum

Available prompt types for different analysis needs.

```python
class PromptType(Enum):
    ANALYZE = "analyze"      # Pattern and trend analysis
    CLASSIFY = "classify"    # Categorization with confidence
    EXTRACT = "extract"      # Entity and relationship extraction
    SUMMARIZE = "summarize"  # Concise summarization
    CUSTOM = "custom"        # Custom instructions
```

## 🎯 Usage Examples

### Example 1: Social Media Analysis

```python
import asyncio
from src.workers import LLMProcess, PromptType

async def analyze_social_media():
    social_data = {
        "tweets": [
            {
                "id": "1",
                "user": "crypto_trader",
                "text": "Bitcoin hitting new resistance at $50k. Time to take profits?",
                "engagement": {"likes": 245, "retweets": 67},
                "timestamp": "2024-01-15T14:30:00Z"
            },
            {
                "id": "2", 
                "user": "market_news",
                "text": "Federal Reserve announces new digital currency framework",
                "engagement": {"likes": 1024, "retweets": 398},
                "timestamp": "2024-01-15T16:45:00Z"
            }
        ],
        "platform_metrics": {
            "total_reach": 50000,
            "engagement_rate": 0.045,
            "trending_topics": ["bitcoin", "fed", "crypto"]
        }
    }
    
    # Analyze content
    analysis = await LLMProcess.analyze_content(social_data)
    print("Content Analysis:")
    print(analysis.result)
    
    # Classify sentiment
    classification = await LLMProcess.classify_data(social_data)
    print("\nClassification:")
    print(classification.result)
    
    # Custom crypto analysis
    crypto_analysis = await LLMProcess.custom_process(
        json_data=social_data,
        custom_instructions="""
        Focus on cryptocurrency-related content and provide:
        1. Sentiment analysis for each crypto mentioned
        2. Market signal strength (1-10 scale)
        3. Key influencer identification
        4. Trend prediction confidence
        5. Risk assessment for traders
        """
    )
    print("\nCrypto Analysis:")
    print(crypto_analysis.result)

asyncio.run(analyze_social_media())
```

### Example 2: E-commerce Data Processing

```python
async def analyze_ecommerce_data():
    ecommerce_data = {
        "orders": [
            {"id": "ORD001", "amount": 129.99, "items": 3, "customer_segment": "premium"},
            {"id": "ORD002", "amount": 45.50, "items": 1, "customer_segment": "standard"},
            {"id": "ORD003", "amount": 310.75, "items": 7, "customer_segment": "premium"}
        ],
        "customer_feedback": [
            {"rating": 5, "comment": "Fast shipping, great quality!"},
            {"rating": 3, "comment": "Product was okay, shipping took too long"},
            {"rating": 5, "comment": "Excellent customer service, will buy again"}
        ],
        "inventory": {
            "low_stock_items": 12,
            "out_of_stock": 3,
            "total_products": 450
        }
    }
    
    # Create custom configuration for detailed analysis
    detailed_config = LLMProcess.create_custom_config(
        model_name="gpt-4o",
        temperature=0.2,  # More deterministic for business analysis
        max_tokens=1200
    )
    
    # Comprehensive business analysis
    business_analysis = await LLMProcess.analyze_content(
        json_data=ecommerce_data,
        provider_name="openai",
        config=detailed_config
    )
    
    print("Business Analysis:")
    print(business_analysis.result)
    
    # Extract key insights
    insights = await LLMProcess.extract_insights(
        json_data=ecommerce_data,
        config=detailed_config
    )
    
    print("\nKey Insights:")
    print(insights.result)

asyncio.run(analyze_ecommerce_data())
```

### Example 3: Batch Processing Multiple Data Sources

```python
async def batch_analysis_example():
    # Multiple data sources to analyze
    data_sources = [
        {
            "source": "twitter",
            "content": "Tesla stock is mooning! 🚀 #TSLA #stocks",
            "metrics": {"followers": 15000, "engagement": 0.08}
        },
        {
            "source": "reddit", 
            "content": "Discussion about Tesla earnings report - mixed signals",
            "metrics": {"upvotes": 234, "comments": 67}
        },
        {
            "source": "news",
            "content": "Tesla reports Q4 earnings beat expectations by 12%",
            "metrics": {"views": 45000, "shares": 890}
        },
        {
            "source": "blog",
            "content": "Technical analysis shows Tesla forming bullish pattern",
            "metrics": {"reads": 5600, "time_spent": "3.2min"}
        }
    ]
    
    # Process all sources in parallel
    print("Processing multiple data sources...")
    
    results = await LLMProcess.batch_process(
        json_data_list=data_sources,
        prompt_type=PromptType.CLASSIFY,
        provider_name="openai",
        max_concurrent=2  # Process 2 at a time
    )
    
    print(f"\nProcessed {len(results)} data sources:")
    
    for i, result in enumerate(results):
        source_name = data_sources[i].get("source", f"Source {i+1}")
        if result.success:
            print(f"\n✅ {source_name.title()}:")
            print(f"   Classification: {result.result[:200]}...")
        else:
            print(f"\n❌ {source_name.title()}: {result.error}")

asyncio.run(batch_analysis_example())
```

## ⚙️ Configuration & Customization

### Custom Prompt Templates

You can override the default prompt templates:

```python
custom_prompt = """
You are a financial data analyst. Analyze this JSON data: {json_data}

Provide analysis in this exact format:
1. MARKET SENTIMENT: [Bullish/Bearish/Neutral]
2. KEY METRICS: [List top 3 metrics]
3. RISK LEVEL: [Low/Medium/High]
4. RECOMMENDATIONS: [Specific action items]
5. CONFIDENCE: [1-10 scale]
"""

result = await LLMProcess.process_json_with_prompt(
    json_data=financial_data,
    custom_prompt=custom_prompt,
    provider_name="anthropic"
)
```

### Provider Selection & Fallback

```python
# Check available providers first
providers = LLMProcess.get_available_providers()
print(f"Available: {providers}")

# The system automatically handles fallback
try:
    # Try primary provider
    result = await LLMProcess.analyze_content(data, provider_name="openai")
except ValueError as e:
    # Will automatically try other available providers
    print(f"Fallback occurred: {e}")
```

### Performance Optimization

```python
# Custom configuration for different use cases
fast_config = LLMProcess.create_custom_config(
    model_name="gpt-4o-mini",  # Faster, cheaper model
    temperature=0.1,           # More deterministic
    max_tokens=500            # Shorter responses
)

detailed_config = LLMProcess.create_custom_config(
    model_name="gpt-4o",      # More capable model
    temperature=0.3,          # Balanced creativity
    max_tokens=2000          # Longer, detailed responses
)

# Use appropriate config for the task
quick_summary = await LLMProcess.summarize_data(data, config=fast_config)
detailed_analysis = await LLMProcess.analyze_content(data, config=detailed_config)
```

## 📋 Best Practices

### 1. Data Preparation
```python
# Clean and structure your JSON data
def prepare_data(raw_data):
    return {
        "processed_data": raw_data,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "source": "data_pipeline",
            "version": "1.0"
        }
    }

data = prepare_data(raw_input)
result = await LLMProcess.analyze_content(data)
```

### 2. Prompt Engineering
```python
# Use specific, structured prompts for better results
detailed_instructions = """
Analyze the e-commerce data and provide insights in JSON format:
{
  "revenue_analysis": "...",
  "customer_insights": "...", 
  "inventory_recommendations": "...",
  "risk_factors": [...],
  "action_items": [...],
  "confidence_score": 0.85
}
"""

result = await LLMProcess.custom_process(
    json_data=ecommerce_data,
    custom_instructions=detailed_instructions
)
```

### 3. Cost Management
```python
# Use appropriate models for different tasks
cost_effective_config = LLMProcess.create_custom_config(
    model_name="gpt-4o-mini",  # Cheaper for simple tasks
    max_tokens=300             # Limit response length
)

# Reserve expensive models for complex analysis
premium_config = LLMProcess.create_custom_config(
    model_name="gpt-4o",       # More capable for complex tasks
    max_tokens=1500
)
```

### 4. Parallel Processing
```python
# Optimize batch processing
async def efficient_batch_processing(large_dataset):
    # Split into smaller batches
    batch_size = 10
    all_results = []
    
    for i in range(0, len(large_dataset), batch_size):
        batch = large_dataset[i:i + batch_size]
        
        batch_results = await LLMProcess.batch_process(
            json_data_list=batch,
            prompt_type=PromptType.CLASSIFY,
            max_concurrent=3  # Avoid rate limits
        )
        
        all_results.extend(batch_results)
        
        # Optional: add delay between batches
        await asyncio.sleep(1)
    
    return all_results
```

## 🔄 Integration Examples

### With Data Pipelines

```python
# Integration with data collection pipeline
from scripts.data_collection import DataCollectionPipeline

async def analyze_collected_data():
    # Collect data
    pipeline = DataCollectionPipeline(session_name="Analysis")
    # ... data collection setup ...
    
    # Process collected data
    for data_file in pipeline.session_dir.glob("*.json"):
        with open(data_file) as f:
            data = json.load(f)
        
        analysis = await LLMProcess.analyze_content(data)
        
        # Save analysis results
        analysis_file = data_file.with_suffix('.analysis.txt')
        with open(analysis_file, 'w') as f:
            f.write(analysis.result)
```

### With Phoenix Pipeline

```python
# Integration with Phoenix data collection
from scripts.phoenix_pipeline import PhoenixPipeline

async def real_time_analysis():
    # Collect data from Phoenix
    phoenix = PhoenixPipeline(api_key="your-key")
    await phoenix.start_collection(duration=300)
    
    # Analyze collected data
    json_files = list(phoenix.pipeline.session_dir.glob("*.jsonl"))
    
    for json_file in json_files:
        with open(json_file) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    
                    # Real-time analysis
                    result = await LLMProcess.classify_data(data)
                    
                    if result.success:
                        print(f"Classification: {result.result}")
```

## 🤝 Extending the LLMProcess system:

1. **Add New Prompt Types**: Extend the `PromptType` enum and add corresponding templates
2. **Custom Analysis Methods**: Add new class methods for specific analysis types
3. **Enhanced Result Processing**: Extend `ProcessingResult` with additional metadata
4. **Performance Optimizations**: Implement caching or result streaming
5. **Integration Helpers**: Add utility methods for common integration patterns

## 📄 License

This worker system is part of the mantlebrain project. See the main project license for details.
