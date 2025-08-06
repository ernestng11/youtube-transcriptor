#!/usr/bin/env python3
"""
YouTube Transcript LLM Processor

Combines YouTube transcript extraction with LLM analysis in a single command.
Usage: poetry run python run_llm_on_transcript.py <video_id>
"""

import os
import sys
import argparse
import json
import time
import asyncio
import yaml
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import dotenv
from youtube_transcriptor.core.pipeline import TranscriptionPipeline
from youtube_transcriptor.core.playlist_extractor import PlaylistExtractor
from youtube_transcriptor.core.transcript_extractor import TranscriptExtractor
from youtube_transcriptor.core.web_transcript_extractor import WebTranscriptExtractor
from youtube_transcriptor.utils.helpers import sanitize_filename
from youtube_transcriptor.config.settings import settings
from workers.llm_process import LLMProcess, PromptType, LLMConfig

# Load environment variables
dotenv.load_dotenv()


class ConfigManager:
    """Manages YAML configuration loading and validation."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load and validate YAML configuration."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Validate required sections
            if 'prompts' not in config:
                raise ValueError("Missing 'prompts' section in config")
            if 'custom' not in config['prompts'] or not config['prompts']['custom']:
                raise ValueError("Missing 'prompts.custom' in config")
            if 'videos' not in config:
                raise ValueError("Missing 'videos' section in config")
            if 'playlists' not in config:
                raise ValueError("Missing 'playlists' section in config")
            
            return config
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
    
    def get_custom_prompt(self) -> str:
        """Get the custom prompt from configuration."""
        return self.config['prompts']['custom']
    
    def is_valid_video_id(self, video_id: str) -> bool:
        """Check if video ID is valid according to config."""
        config_video_id = self.config['videos'].get('id', '')
        return config_video_id == '' or config_video_id == video_id
    
    def is_valid_playlist_id(self, playlist_id: str) -> bool:
        """Check if playlist ID is valid according to config."""
        config_playlist_id = self.config['playlists'].get('id', '')
        return config_playlist_id == '' or config_playlist_id == playlist_id
    
    def is_valid_id(self, id_str: str) -> bool:
        """Check if ID is valid for either videos or playlists."""
        return self.is_valid_video_id(id_str) or self.is_valid_playlist_id(id_str)


class YouTubeLLMProcessor:
    """Combined processor for YouTube transcript extraction and LLM analysis."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize the processor with API keys from environment."""
        self.config_manager = config_manager
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.transcript_api_token = os.getenv("TRANSCRIPT_API_TOKEN")
        
        if not self.youtube_api_key:
            raise ValueError("YOUTUBE_API_KEY environment variable is required")
        
        self.use_web_api = bool(self.transcript_api_token)
        
        print(f"🔧 Initialized YouTube LLM Processor")
        print(f"✅ YouTube API: {'SET' if self.youtube_api_key else '❌ NOT SET'}")
        print(f"✅ Transcript API: {'SET' if self.transcript_api_token else '❌ NOT SET (using fallback)'}")
        print(f"📄 Config: {self.config_manager.config_path}")
        print()
    
    def get_video_info(self, video_id: str) -> dict:
        """Get video information using YouTube API."""
        try:
            # Try to get video info using the web transcript API first
            if self.use_web_api:
                web_extractor = WebTranscriptExtractor(self.transcript_api_token)
                response = web_extractor._make_api_request([video_id])
                if response and len(response) > 0:
                    video_data = response[0]
                    return {
                        "title": video_data.get('title', f'Video {video_id}'),
                        "channel_title": video_data.get('author', 'Unknown'),
                        "description": video_data.get('microformat', {}).get('playerMicroformatRenderer', {}).get('description', {}).get('simpleText', ''),
                        "view_count": video_data.get('microformat', {}).get('playerMicroformatRenderer', {}).get('viewCount'),
                        "published_at": None,
                        "duration_seconds": None,
                        "like_count": video_data.get('likeCount')
                    }
            
            # Fallback to basic info
            return {
                "title": f"Video {video_id}",
                "channel_title": "Unknown",
                "description": "",
                "view_count": None,
                "published_at": None,
                "duration_seconds": None,
                "like_count": None
            }
            
        except Exception as e:
            print(f"Warning: Could not get video metadata: {e}")
            return {
                "title": f"Video {video_id}",
                "channel_title": "Unknown",
                "description": "",
                "view_count": None,
                "published_at": None,
                "duration_seconds": None,
                "like_count": None
            }
    
    def extract_transcript(self, video_id: str) -> dict:
        """Extract transcript for a single video."""
        print(f"🎥 Processing Video ID: {video_id}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # Get video metadata
            video_info = self.get_video_info(video_id)
            
            # Extract transcript
            transcript_extractor = TranscriptExtractor(use_web_api=self.use_web_api)
            transcript = transcript_extractor.extract_video_transcript(video_id, video_info['title'])
            
            if not transcript:
                raise Exception("Failed to extract transcript")
            
            # Aggregate transcript text
            aggregated_text = " ".join(segment.text for segment in transcript.segments if segment.text.strip())
            aggregated_text = " ".join(aggregated_text.split())  # Clean up whitespace
            
            # Create comprehensive video data
            video_data = {
                "video_id": video_id,
                "video_title": video_info['title'],
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "channel_title": video_info.get('channel_title', 'Unknown'),
                "published_at": video_info.get('published_at'),
                "duration_seconds": video_info.get('duration_seconds'),
                "view_count": video_info.get('view_count'),
                "like_count": video_info.get('like_count'),
                "description": video_info.get('description', ''),
                
                # Transcript data
                "transcript": {
                    "language": transcript.language,
                    "is_auto_generated": transcript.is_auto_generated,
                    "total_segments": len(transcript.segments),
                    "aggregated_text": aggregated_text,
                    "text_length": len(aggregated_text),
                    "word_count": len(aggregated_text.split()) if aggregated_text else 0
                },
                
                # Metadata
                "extraction_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "processing_type": "single_video"
            }
            
            total_time = time.time() - start_time
            
            print(f"✅ Transcript extracted successfully!")
            print(f"📹 Video: {video_info['title']}")
            print(f"🎭 Channel: {video_info.get('channel_title', 'Unknown')}")
            print(f"🌍 Language: {transcript.language}")
            print(f"📊 Segments: {len(transcript.segments)}")
            print(f"📝 Words: {video_data['transcript']['word_count']:,}")
            print(f"⏱️  Extraction Time: {total_time:.2f}s")
            print()
            
            return video_data
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            raise
    
    async def process_with_llm(self, video_data: dict, provider: str = "openai", 
                              model: str = "gpt-4o-mini") -> str:
        """Process the transcript with LLM analysis."""
        print(f"🤖 Processing with LLM ({provider}/{model})")
        print("-" * 50)
        
        start_time = time.time()
        
        # Extract the specific fields from the JSON data
        video_title = video_data.get("video_title", "Unknown Title")
        description = video_data.get("description", "No description available")
        transcript_text = video_data.get("transcript", {}).get("aggregated_text", "No transcript available")
        
        # Get custom prompt from config
        custom_prompt = self.config_manager.get_custom_prompt()
        
        # Use custom prompt with video context or default structured prompt
        if custom_prompt:
            prompt = f"""
Video Title: {video_title}

Video Description: {description}

Transcript: {transcript_text}

{custom_prompt}
"""
        else:
            prompt = f"""
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
        
        # Create LLM configuration
        config = LLMConfig(
            model_name=model,
            temperature=0.2,
            max_tokens=16384
        )
        
        # Process with LLM
        result = await LLMProcess.process_text_with_prompt(
            text_data=prompt,
            prompt_type=PromptType.CUSTOM,
            custom_prompt=prompt,
            provider_name=provider,
            config=config
        )
        
        total_time = time.time() - start_time
        
        if result.success:
            print(f"✅ LLM processing completed!")
            print(f"⏱️  Processing Time: {total_time:.2f}s")
            print()
            return result.result
        else:
            raise Exception(f"LLM processing failed: {result.error}")
    
    async def run(self, video_id: str, provider: str = "openai", 
                  model: str = "gpt-4o-mini") -> str:
        """Main execution flow: extract transcript and process with LLM."""
        try:
            # Validate video ID against config
            if not self.config_manager.is_valid_id(video_id):
                raise ValueError(f"Video/Playlist ID '{video_id}' is not configured in config.yaml")
            
            # Step 1: Extract transcript
            video_data = self.extract_transcript(video_id)
            
            # Step 2: Process with LLM
            llm_result = await self.process_with_llm(video_data, provider, model)
            
            return llm_result
            
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            raise


def main():
    """Main entry point for the YouTube LLM Processor."""
    parser = argparse.ArgumentParser(
        description="YouTube Transcript LLM Processor - Extract transcript and analyze with LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  poetry run python run_llm_on_transcript.py
  poetry run python run_llm_on_transcript.py --config custom_config.yaml

Environment Variables:
  YOUTUBE_API_KEY       - Required YouTube Data API v3 key
  TRANSCRIPT_API_TOKEN  - Optional youtube-transcript.io API token (recommended)
  OPENAI_API_KEY        - Required for OpenAI provider
  ANTHROPIC_API_KEY     - Required for Anthropic provider
        """
    )
    
    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="Path to YAML configuration file (default: config.yaml)"
    )
    
    args = parser.parse_args()
    
    # Print header
    print("🎬 YouTube Transcript LLM Processor")
    print("=" * 50)
    
    try:
        # Load configuration
        config_manager = ConfigManager(args.config)
        
        # Get video/playlist ID from config
        video_id = config_manager.config['videos'].get('id', '')
        playlist_id = config_manager.config['playlists'].get('id', '')
        
        if not video_id and not playlist_id:
            raise ValueError("No video or playlist ID configured in config.yaml")
        
        # Use video ID if available, otherwise playlist ID
        target_id = video_id if video_id else playlist_id
        
        # Initialize processor
        processor = YouTubeLLMProcessor(config_manager)
        
        # Run processing
        result = asyncio.run(processor.run(
            video_id=target_id,
            provider="openai",  # Default provider
            model="gpt-4o-mini"  # Default model
        ))
        
        print("=" * 50)
        print("📋 ANALYSIS RESULTS")
        print("=" * 50)
        print(result)
        
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 