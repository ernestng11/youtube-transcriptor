"""
LLM Processing Worker

A worker class that uses the LLM providers system to process JSON input
with custom prompts for various analysis tasks.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

# Import LLM providers system
from llm_providers import LLMProviderFactory, LLMConfig, BaseLLMProvider

# Configure logging
logger = logging.getLogger(__name__)


class PromptType(Enum):
    """Enum for different types of prompts"""
    ANALYZE = "analyze"
    CLASSIFY = "classify"
    EXTRACT = "extract"
    SUMMARIZE = "summarize"
    CUSTOM = "custom"
    SENTIMENT = "sentiment"  # Example: New sentiment analysis prompt
    TRADING = "trading"      # Example: Trading signals prompt


@dataclass
class ProcessingResult:
    """Result of LLM processing"""
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    prompt_type: Optional[str] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None


class LLMProcess:
    """
    LLM Processing Worker that provides class methods for processing JSON input
    with custom prompts using the LLM providers system.
    """
    
    # Class-level factory instance
    _factory: Optional[LLMProviderFactory] = None
    
    # Default configuration
    DEFAULT_CONFIG = LLMConfig(
        model_name="gpt-4o-mini",  # Fast and cost-effective
        temperature=0.3,           # Relatively deterministic
        max_tokens=50000           # Reasonable limit
    )
    
    # Placeholder prompts - to be customized later
    PLACEHOLDER_PROMPTS = {
        PromptType.ANALYZE: """
You are an expert data analyst. Analyze the following JSON data and provide insights.

{json_data}

Format your response as structured analysis with clear sections.
""",
        
        PromptType.CLASSIFY: """
You are an expert classifier. Classify the following JSON data into appropriate categories.

JSON Data:
{json_data}

Please provide:
1. Primary category
2. Secondary categories (if applicable)
3. Confidence level (1-10)
4. Reasoning for classification

Format your response as structured classification with clear categories.
""",
        
        PromptType.EXTRACT: """
-Goal-
Given a text document that is potentially relevant to this activity, first identify all entities needed from the text in order to capture the information and ideas in the text.
Next, report all relationships among the identified entities.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: Suggest several labels or categories for the entity. The categories should not be specific, but should be as general as possible.
- entity_description: Comprehensive description of the entity's attributes and activities
Format each entity as ("entity"<|><entity_name><|><entity_type><|><entity_description>

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
 Format each relationship as ("relationship"<|><source_entity><|><target_entity><|><relationship_description><|><relationship_strength>)

3. Return output in English as a single list of all the entities and relationships identified in steps 1 and 2. Use **<|>** as the list delimiter.

4. When finished, output <|COMPLETE|>

-Examples-
######################

Example 1:

text:
It was very dark, and the wind howled horribly around her, but Dorothy
found she was riding quite easily. After the first few whirls around,
and one other time when the house tipped badly, she felt as if she were
being rocked gently, like a baby in a cradle.

Toto did not like it. He ran about the room, now here, now there,
barking loudly; but Dorothy sat quite still on the floor and waited to
see what would happen.

Once Toto got too near the open trap door, and fell in; and at first
the little girl thought she had lost him. But soon she saw one of his
ears sticking up through the hole, for the strong pressure of the air
was keeping him up so that he could not fall. She crept to the hole,
caught Toto by the ear, and dragged him into the room again, afterward
closing
------------------------
output:
("entity"<|>DOROTHY<|>CHARACTER, PERSON<|>Dorothy is a character who experiences a dark and windy environment, feels as if being rocked gently, and actively participates in rescuing Toto)
<|>
("entity"<|>TOTO<|>CHARACTER, ANIMAL<|>Toto is Dorothy's dog who dislikes the situation, runs around barking, and accidentally falls into a trap door but is saved by Dorothy)
<|>
("entity"<|>TRAP DOOR<|>OBJECT<|>The trap door is an opening through which Toto falls, but the air pressure prevents him from falling completely)
<|>
("relationship"<|>DOROTHY<|>TOTO<|>Dorothy rescues Toto from the trap door, showing a caring relationship<|>9)
<|>
("relationship"<|>TOTO<|>TRAP DOOR<|>Toto falls into the trap door, which is a pivotal moment for his character in this scene<|>7)
<|>
("relationship"<|>DOROTHY<|>TRAP DOOR<|>Dorothy interacts with the trap door to rescue Toto, showing her proactive nature<|>8)
<|COMPLETE|>
#############################



-Real Data-
######################
text: {json_data}
######################
output:
""",
        
        PromptType.SUMMARIZE: """
You are an expert summarizer. Summarize the following JSON data concisely.

JSON Data:
{json_data}

Please provide:
1. Executive summary (2-3 sentences)
2. Key points (bullet format)
3. Important metrics or numbers
4. Overall context

Format your response as a clear, concise summary.
""",
        
        PromptType.CUSTOM: """
Process the following JSON data according to the specific instructions provided.

JSON Data:
{json_data}


Please follow the instructions exactly and provide a structured response.
""",

        # Custom prompt types added below
        PromptType.SENTIMENT: """
You are an expert sentiment analyst. Analyze the sentiment of the following JSON data.

JSON Data:
{json_data}

Please provide:
1. Overall sentiment score (-1 to +1, where -1 is very negative, 0 is neutral, +1 is very positive)
2. Sentiment breakdown by content type
3. Key emotional indicators found
4. Sentiment trends and patterns
5. Confidence level in the analysis

Format your response as a structured sentiment analysis report.
""",

        PromptType.TRADING: """
You are an expert trading analyst. Analyze the following market data and provide trading insights.

JSON Data:
{json_data}

Please provide:
1. Trading signal (BUY/SELL/HOLD)
2. Risk assessment (LOW/MEDIUM/HIGH)
3. Price targets and stop-loss levels
4. Market momentum indicators
5. Time horizon recommendation
6. Position sizing suggestions

Format your response as a professional trading analysis report.
"""
    }
    
    @classmethod
    def get_factory(cls) -> LLMProviderFactory:
        """Get or create the LLM provider factory instance"""
        if cls._factory is None:
            cls._factory = LLMProviderFactory()
        return cls._factory
    
    @classmethod
    def get_provider(cls, provider_name: str = "openai") -> BaseLLMProvider:
        """
        Get LLM provider with validation.
        
        Args:
            provider_name: Name of the provider ("openai" or "anthropic")
            
        Returns:
            BaseLLMProvider: Initialized provider
            
        Raises:
            ValueError: If provider not available or API key missing
        """
        factory = cls.get_factory()
        
        try:
            return factory.get_provider(provider_name)
        except ValueError as e:
            # Try fallback provider
            available_providers = factory.validate_all_providers()
            for provider, is_available in available_providers.items():
                if is_available and provider != provider_name:
                    logger.warning(f"Primary provider '{provider_name}' not available, using '{provider}' as fallback")
                    return factory.get_provider(provider)
            
            # No providers available
            raise ValueError(f"No LLM providers available. Available providers: {list(available_providers.keys())}. Error: {e}")
    
    @classmethod
    async def process_json_with_prompt(
        cls,
        json_data: Union[Dict[str, Any], str],
        prompt_type: PromptType = PromptType.ANALYZE,
        custom_prompt: Optional[str] = None,
        custom_instructions: Optional[str] = None,
        provider_name: str = "openai",
        config: Optional[LLMConfig] = None
    ) -> ProcessingResult:
        """
        Main method to process JSON data with custom prompts.
        
        Args:
            json_data: JSON data as dict or string
            prompt_type: Type of prompt to use
            custom_prompt: Custom prompt template (overrides prompt_type)
            custom_instructions: Custom instructions for CUSTOM prompt type
            provider_name: LLM provider to use
            config: LLM configuration (uses default if None)
            
        Returns:
            ProcessingResult: Result of the processing
        """
        try:
            # Prepare JSON data
            if isinstance(json_data, str):
                try:
                    json_data = json.loads(json_data)
                except json.JSONDecodeError as e:
                    return ProcessingResult(
                        success=False,
                        error=f"Invalid JSON string: {e}",
                        input_data=None
                    )
            
            # Format JSON for prompt
            json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
            
            # Get provider
            provider = cls.get_provider(provider_name)
            
            # Use provided config or default
            if config is None:
                config = cls.DEFAULT_CONFIG
            
            # Prepare prompt
            if custom_prompt:
                # Use custom prompt directly
                prompt_template = custom_prompt
                formatted_prompt = prompt_template.format(
                    json_data=json_str,
                    custom_instructions=custom_instructions or ""
                )
            else:
                # Use predefined prompt template
                prompt_template = cls.PLACEHOLDER_PROMPTS[prompt_type]
                
                if prompt_type == PromptType.CUSTOM:
                    if not custom_instructions:
                        return ProcessingResult(
                            success=False,
                            error="Custom instructions required for CUSTOM prompt type",
                            input_data=json_data if isinstance(json_data, dict) else None
                        )
                    formatted_prompt = prompt_template.format(
                        json_data=json_str,
                        custom_instructions=custom_instructions
                    )
                else:
                    formatted_prompt = prompt_template.format(json_data=json_str)
            
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert AI assistant specialized in data analysis and processing. Provide accurate, structured, and actionable responses."
                },
                {
                    "role": "user",
                    "content": formatted_prompt
                }
            ]
            
            # Generate response
            response = await provider.generate_response(messages, config)
            
            return ProcessingResult(
                success=True,
                result=response,
                input_data=json_data if isinstance(json_data, dict) else None,
                prompt_type=prompt_type.value,
                model_used=config.model_name
            )
            
        except Exception as e:
            logger.error(f"Error processing JSON with LLM: {e}")
            return ProcessingResult(
                success=False,
                error=str(e),
                input_data=json_data if isinstance(json_data, dict) else None,
                prompt_type=prompt_type.value if prompt_type else None
            )
    
    @classmethod
    async def process_text_with_prompt(
        cls,
        text_data: str,
        prompt_type: PromptType = PromptType.ANALYZE,
        custom_prompt: Optional[str] = None,
        custom_instructions: Optional[str] = None,
        provider_name: str = "openai",
        config: Optional[LLMConfig] = None
    ) -> ProcessingResult:
        """
        Process text data with custom prompts.
        
        Args:
            text_data: Text data to process
            prompt_type: Type of prompt to use
            custom_prompt: Custom prompt template (overrides prompt_type)
            custom_instructions: Custom instructions for CUSTOM prompt type
            provider_name: LLM provider to use
            config: LLM configuration (uses default if None)
            
        Returns:
            ProcessingResult: Result of the processing
        """
        try:
            # Validate text input
            if not text_data or not isinstance(text_data, str):
                return ProcessingResult(
                    success=False,
                    error="Text data must be a non-empty string",
                    input_data=None
                )
            
            # Get provider
            provider = cls.get_provider(provider_name)
            
            # Use provided config or default
            if config is None:
                config = cls.DEFAULT_CONFIG
            
            # Prepare prompt
            if custom_prompt:
                # Use custom prompt directly
                prompt_template = custom_prompt
                formatted_prompt = prompt_template.format(
                    text_data=text_data,
                    custom_instructions=custom_instructions or ""
                )
            else:
                # Use predefined prompt template (replace json_data with text_data)
                prompt_template = cls.PLACEHOLDER_PROMPTS[prompt_type]
                
                if prompt_type == PromptType.CUSTOM:
                    if not custom_instructions:
                        return ProcessingResult(
                            success=False,
                            error="Custom instructions required for CUSTOM prompt type",
                            input_data={"text": text_data}
                        )
                    formatted_prompt = prompt_template.format(
                        json_data=text_data,  # Keep json_data for compatibility
                        custom_instructions=custom_instructions
                    )
                else:
                    formatted_prompt = prompt_template.format(json_data=text_data)
            
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert AI assistant specialized in text analysis and processing. Provide accurate, structured, and actionable responses."
                },
                {
                    "role": "user",
                    "content": formatted_prompt
                }
            ]
            
            # Debug: Print the messages being sent to the LLM
            print("=== MESSAGES BEING SENT TO LLM ===")
            for i, message in enumerate(messages):
                print(f"Message {i+1} ({message['role']}):")
                print(f"Content: {message['content']}")
                print("-" * 50)
            print("==================================")
            
            # Generate response
            response = await provider.generate_response(messages, config)
            
            return ProcessingResult(
                success=True,
                result=response,
                input_data={"text": text_data},
                prompt_type=prompt_type.value,
                model_used=config.model_name
            )
            
        except Exception as e:
            logger.error(f"Error processing text with LLM: {e}")
            return ProcessingResult(
                success=False,
                error=str(e),
                input_data={"text": text_data},
                prompt_type=prompt_type.value if prompt_type else None
            )
    
    @classmethod
    async def batch_process(
        cls,
        json_data_list: List[Union[Dict[str, Any], str]],
        prompt_type: PromptType = PromptType.ANALYZE,
        provider_name: str = "openai",
        config: Optional[LLMConfig] = None,
        max_concurrent: int = 3
    ) -> List[ProcessingResult]:
        """
        Process multiple JSON data items in parallel.
        
        Args:
            json_data_list: List of JSON data to process
            prompt_type: Type of prompt to use
            provider_name: LLM provider to use
            config: LLM configuration
            max_concurrent: Maximum concurrent processes
            
        Returns:
            List[ProcessingResult]: List of processing results
        """
        import asyncio
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single(json_data):
            async with semaphore:
                return await cls.process_json_with_prompt(
                    json_data=json_data,
                    prompt_type=prompt_type,
                    provider_name=provider_name,
                    config=config
                )
        
        # Process all items concurrently
        tasks = [process_single(json_data) for json_data in json_data_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to ProcessingResult
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                input_item = json_data_list[i] if i < len(json_data_list) else None
                processed_results.append(ProcessingResult(
                    success=False,
                    error=str(result),
                    input_data=input_item if isinstance(input_item, dict) else None
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, bool]:
        """
        Get status of available LLM providers.
        
        Returns:
            Dict[str, bool]: Provider availability status
        """
        factory = cls.get_factory()
        return factory.validate_all_providers()
    
    @classmethod
    def create_custom_config(
        cls,
        model_name: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        **additional_params
    ) -> LLMConfig:
        """
        Create custom LLM configuration.
        
        Args:
            model_name: Model to use (provider default if None)
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum response length
            **additional_params: Provider-specific parameters
            
        Returns:
            LLMConfig: Custom configuration
        """
        return LLMConfig(
            model_name=model_name or cls.DEFAULT_CONFIG.model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            additional_params=additional_params
        ) 