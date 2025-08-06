#!/usr/bin/env python3
"""
Process JSON transcript data using LLM and save results to text files.
"""

import json
import asyncio
import os
from datetime import datetime
from pathlib import Path
from data_reader import traverse_json_files
from result_parser import split_llm_result, parse_entities_and_relationships, save_parsed_result

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed. Make sure OPENAI_API_KEY is set in environment.")

# Try to import workers module
try:
    from workers import LLMProcess, PromptType
    WORKERS_AVAILABLE = True
    print("✅ Workers module loaded successfully")
except ImportError:
    WORKERS_AVAILABLE = False
    print("⚠️  Workers module not found. LLM processing will be skipped.")


def save_result_to_file(result: str, filename: str, output_dir: str = "results") -> str:
    """
    Save processing result to a text file.
    
    Args:
        result: The text result to save
        filename: Base filename (without extension)
        output_dir: Directory to save files in
        
    Returns:
        Path to the saved file
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
    output_file = output_path / f"{safe_filename}_{timestamp}.txt"
    
    # Save result to file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Processing Result for: {filename}\n")
            f.write(f"# Generated at: {datetime.now().isoformat()}\n")
            f.write(f"# {'=' * 50}\n\n")
            f.write(result)
        
        print(f"💾 Result saved to: {output_file}")
        return str(output_file)
        
    except Exception as e:
        print(f"❌ Error saving result to file: {e}")
        return ""


def save_transcript_summary(data: dict, output_dir: str = "results") -> str:
    """
    Save a simple transcript summary to text file (fallback when LLM not available).
    
    Args:
        data: JSON data containing transcript
        output_dir: Directory to save files in
        
    Returns:
        Path to the saved file
    """
    try:
        video_title = data.get('video_title', 'Unknown Video')
        transcript_data = data.get('transcript', {})
        
        # Create summary text
        summary = f"Video Title: {video_title}\n"
        summary += f"Channel: {data.get('channel_title', 'Unknown')}\n"
        summary += f"Duration: {data.get('duration_seconds', 0)} seconds\n"
        summary += f"Language: {transcript_data.get('language', 'Unknown')}\n"
        summary += f"Word Count: {transcript_data.get('word_count', 0):,}\n"
        summary += f"Total Segments: {transcript_data.get('total_segments', 0)}\n"
        summary += f"Auto Generated: {transcript_data.get('is_auto_generated', 'Unknown')}\n"
        summary += "\n" + "=" * 50 + "\n"
        summary += "FULL TRANSCRIPT:\n"
        summary += "=" * 50 + "\n\n"
        summary += transcript_data.get('aggregated_text', 'No transcript text available')
        
        return save_result_to_file(summary, video_title, output_dir)
        
    except Exception as e:
        print(f"❌ Error creating transcript summary: {e}")
        return ""


async def process_with_llm(data: dict, provider_name: str) -> str:
    """
    Process transcript data using LLM.
    
    Args:
        data: JSON data containing transcript
        provider_name: Name of the LLM provider to use
        
    Returns:
        Processed result as string
    """
    try:
        transcript_data = data.get("transcript", {})
        message_data = json.dumps(transcript_data)
        
        result = await LLMProcess.process_json_with_prompt(
            message_data,
            prompt_type=PromptType.EXTRACT,
            provider_name=provider_name
        )
        
        return str(result)
        
    except Exception as e:
        print(f"❌ Error processing with LLM: {e}")
        return f"Error: {e}"


async def main():
    """Main processing function."""
    print("🎬 YouTube Transcript Processor")
    print("=" * 50)
    
    processed_count = 0
    
    for data in traverse_json_files(limit=10, data_path="data"):
        try:
            video_title = data.get('video_title', data.get('_file_name', 'Unknown'))
            print(f"\n📹 Processing: {video_title}")
            
            if WORKERS_AVAILABLE:
                # Check LLM provider availability
                providers = LLMProcess.get_available_providers()
                available_provider = None
                
                for provider_name, is_available in providers.items():
                    if is_available:
                        available_provider = provider_name
                        break
                
                if available_provider:
                    print(f"✅ Using LLM provider: {available_provider}")
                    
                    # Process with LLM
                    result = await process_with_llm(data, available_provider)
                    
                    # Parse LLM result using split_llm_result
                    print(f"🔍 Parsing LLM result...")
                    items = split_llm_result(str(result))
                    parsed_data = parse_entities_and_relationships(str(result))
                    
                    print(f"📊 Found {parsed_data['total_items']} items")
                    print(f"🏢 Entities: {parsed_data['entity_count']}")
                    print(f"🔗 Relationships: {parsed_data['relationship_count']}")
                    
                    # Save raw LLM result to file
                    output_file = save_result_to_file(
                        str(result), 
                        f"llm_processed_{video_title}",
                        "results/llm_processed"
                    )
                    
                    # Save parsed result to file
                    parsed_output_file = save_parsed_result(
                        str(result),
                        f"parsed_{video_title}",
                        "results/parsed"
                    )
                    
                    print(f"📄 Raw result: {output_file}")
                    print(f"📋 Parsed result: {parsed_output_file}")
                    
                else:
                    print("❌ No LLM providers available. Saving transcript summary instead.")
                    output_file = save_transcript_summary(data, "results/transcript_summaries")
            else:
                print("📝 Workers module not available. Saving transcript summary.")
                output_file = save_transcript_summary(data, "results/transcript_summaries")
            
            if output_file:
                processed_count += 1
                print(f"✅ Processed and saved: {video_title}")
            else:
                print(f"❌ Failed to process: {video_title}")
                
        except Exception as e:
            print(f"❌ Error processing data: {e}")
            continue
    
    print(f"\n🎉 Processing complete! Processed {processed_count} files.")
    print(f"📁 Check results in the 'results/' directory")


if __name__ == "__main__":
    asyncio.run(main())
