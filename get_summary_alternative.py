import asyncio
from workers.llm_process import LLMProcess, PromptType, LLMConfig

async def summarize_json_transcript_alternative(json_input):
    # Create custom LLM configuration
    config = LLMConfig(
        model_name="gpt-4o",
        temperature=0.2,
        max_tokens=128000
    )
    
    # Extract the specific fields from the JSON data
    video_title = json_input.get("video_title", "Unknown Title")
    description = json_input.get("description", "No description available")
    transcript_text = json_input.get("transcript", {}).get("aggregated_text", "No transcript available")
    
    # Use custom_instructions to pass the extracted data
    custom_instructions = f"""
Video Title: {video_title}
Video Description: {description}
Transcript: {transcript_text}

You are an expert content writer tasked with producing a comprehensive article based solely on the video transcript above.

**Instructions:**
1. Break down the transcript into smaller chunks - What it is, how it works and why it matters.
2. For each chunk, write a summary.
3. Only use content from the transcript.

Begin only after fully processing the transcript content. Do not summarize—write a detailed, structured article.
"""
    
    # Use process_json_with_prompt with CUSTOM prompt type
    result = await LLMProcess.process_json_with_prompt(
        json_data=json_input,
        prompt_type=PromptType.CUSTOM,
        provider_name="openai",
        custom_instructions=custom_instructions,
        config=config
    )
    
    if result.success:
        print("Analysis result:", result.result)
    else:
        print("Error:", result.error)

# Run the analysis
# Load JSON data from file
import json
from pathlib import Path

json_file = Path("data/EthCC[8]RedfordStage/AdamLevine(Fireblocks)-UnlockingthePotentialofCross-ChainBridgingforEnterprises_jTf3MNp6S7E.json")

with open(json_file, 'r', encoding='utf-8') as f:
    json_data = json.load(f)

asyncio.run(summarize_json_transcript_alternative(json_data)) 