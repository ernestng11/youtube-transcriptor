import asyncio
from workers.llm_process import LLMProcess, PromptType, LLMConfig
import dotenv

dotenv.load_dotenv()

async def summarize_json_transcript(json_input):
    # Create custom LLM configuration
    config = LLMConfig(
        model_name="gpt-4.1",
        temperature=0.2,
        max_tokens=16384
    )
    
    # Extract the specific fields from the JSON data
    video_title = json_input.get("video_title", "Unknown Title")
    description = json_input.get("description", "No description available")
    transcript_text = json_input.get("transcript", {}).get("aggregated_text", "No transcript available")
    
    # Pre-format the custom prompt with the extracted values
    custom_prompt = f"""
You are an expert technical writer and editor specializing in artificial intelligence and emerging technologies. You excel at transforming complex transcripts into clear, structured, and engaging articles for both technical and non-technical audiences. Your approach is analytical and factual: you rely solely on the given transcript, avoid assumptions, and organize information in a logical, reader-friendly way. Your writing is concise, professional, and geared toward conveying both the details and the significance of the topic.
* **Video Title:** {video_title}
* **Video Description:** {description}
* **Transcript:** {transcript_text}

**Instructions:**
Segment the transcript into three logical sections based strictly on the content:

1. What it is: Explain what the topic, tool, or concept is.

2. How it works: Describe how it functions, operates, or is used.

3. Why it matters: Summarize its significance, impact, or relevance.

For each section, write a concise summary using only information from the transcript to prevent hallucination.

Each summary should be clear, factual, and self-contained.

Avoid introducing any external information or assumptions.

Format your output as follows:

What it is: [Your summary here in bullet points]

How it works: [Your summary here in bullet points]

Why it matters: [Your summary here in bullet points]

Begin only after fully processing the transcript content. Do not summarize—write a detailed, structured article.
"""
#     custom_prompt = f"""
# You are an expert technical writer and editor specializing in artificial intelligence and emerging technologies. You excel at transforming complex transcripts into clear, structured, and engaging articles for both technical and non-technical audiences. Your approach is analytical and factual: you rely solely on the given transcript, avoid assumptions, and organize information in a logical, reader-friendly way. Your writing is concise, professional, and geared toward conveying both the details and the significance of the topic.
# * **Video Title:** {video_title}
# * **Video Description:** {description}
# * **Transcript:** {transcript_text}

# Instructions:

# Carefully read and analyze the entire transcript to understand the content.

# Extract only relevant insights that accurately support or explain the video description.

# Do not invent or infer any information that is not directly present in the transcript.

# Your final output should be a well-structured, full-length article that expands upon and clarifies the video description using the transcript as your only source.

# Maintain a clear, informative tone. Aim for coherence, logical flow, and completeness.

# Begin only after fully processing the transcript content. Do not summarize. Write a detailed, structured article.
# """
    
    # Use process_text_with_prompt with the pre-formatted prompt
    result = await LLMProcess.process_text_with_prompt(
        text_data=custom_prompt,
        provider_name="openai",
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

json_file = Path("data/Anthropic_InverseScalinginTest-TimeCompute/Anthropic_InverseScalinginTest-TimeCompute_dkmGW6PnYNE.json")


with open(json_file, 'r', encoding='utf-8') as f:
    json_data = json.load(f)

asyncio.run(summarize_json_transcript(json_data))