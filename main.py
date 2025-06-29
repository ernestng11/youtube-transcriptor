#!/usr/bin/env python3
"""
Official YouTube Transcriptor Main Script

Processes YouTube playlist or video URLs and saves organized transcript files.
Supports both playlist and individual video processing with automatic organization.

Usage:
    python main.py "https://www.youtube.com/playlist?list=PLAYLIST_ID"
    python main.py "https://www.youtube.com/watch?v=VIDEO_ID"
    python main.py --help
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from youtube_transcriptor.core.pipeline import TranscriptionPipeline
from youtube_transcriptor.core.playlist_extractor import PlaylistExtractor
from youtube_transcriptor.core.transcript_extractor import TranscriptExtractor
from youtube_transcriptor.core.web_transcript_extractor import WebTranscriptExtractor
from youtube_transcriptor.utils.helpers import sanitize_filename
from youtube_transcriptor.config.settings import settings


class YouTubeProcessor:
    """Main processor for YouTube URLs (both playlists and videos)."""
    
    def __init__(self):
        """Initialize the processor with API keys from environment."""
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.transcript_api_token = os.getenv("TRANSCRIPT_API_TOKEN")
        
        if not self.youtube_api_key:
            raise ValueError("YOUTUBE_API_KEY environment variable is required")
        
        self.use_web_api = bool(self.transcript_api_token)
        
        print(f"🔧 Initialized YouTube Processor")
        print(f"✅ YouTube API: {'SET' if self.youtube_api_key else '❌ NOT SET'}")
        print(f"✅ Transcript API: {'SET' if self.transcript_api_token else '❌ NOT SET (using fallback)'}")
        print()
    
    def identify_url_type(self, url: str) -> tuple[str, str]:
        """
        Identify if URL is a playlist or video and extract the ID.
        
        Args:
            url: YouTube URL or ID
            
        Returns:
            Tuple of (type, id) where type is 'playlist' or 'video'
        """
        # Handle direct IDs
        if not url.startswith('http'):
            if len(url) == 11:  # Video ID length
                return 'video', url
            elif len(url) > 11:  # Assume playlist ID
                return 'playlist', url
        
        # Parse URL
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Check for playlist
        if 'list' in query_params:
            playlist_id = query_params['list'][0]
            return 'playlist', playlist_id
        
        # Check for video
        if 'v' in query_params:
            video_id = query_params['v'][0]
            return 'video', video_id
        
        # Check for youtu.be format
        if parsed.hostname == 'youtu.be':
            video_id = parsed.path[1:]  # Remove leading slash
            return 'video', video_id
        
        raise ValueError(f"Could not identify URL type: {url}")
    
    def process_playlist(self, playlist_url: str, base_output_dir: str = "data") -> dict:
        """Process a YouTube playlist."""
        print(f"🎬 Processing Playlist: {playlist_url}")
        print("-" * 50)
        
        # Use the existing pipeline
        pipeline = TranscriptionPipeline(
            youtube_api_key=self.youtube_api_key,
            use_web_api=self.use_web_api
        )
        
        start_time = time.time()
        results = pipeline.process_playlist(playlist_url, base_output_dir)
        total_time = time.time() - start_time
        
        if results["success"]:
            playlist_data = results["playlist_data"]
            print(f"✅ SUCCESS!")
            print(f"📋 Playlist: {playlist_data['title']}")
            print(f"🎭 Channel: {playlist_data['channel']}")
            print(f"📊 Videos: {playlist_data['video_count']}")
            print(f"✅ Transcripts: {results['transcripts_processed']}")
            print(f"❌ Failed: {results['transcripts_failed']}")
            print(f"📈 Success Rate: {(results['transcripts_processed']/playlist_data['video_count']*100):.1f}%")
            print(f"⏱️  Processing Time: {total_time:.2f}s")
            print(f"📁 Output Directory: {results['output_directory']}")
        else:
            print(f"❌ FAILED!")
            for error in results["errors"]:
                print(f"  • {error}")
        
        return results
    
    def process_video(self, video_url: str, base_output_dir: str = "data") -> dict:
        """Process a single YouTube video."""
        _, video_id = self.identify_url_type(video_url)
        
        print(f"🎥 Processing Video: {video_url}")
        print(f"🆔 Video ID: {video_id}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # Extract video metadata using playlist extractor (single video)
            playlist_extractor = PlaylistExtractor(self.youtube_api_key)
            
            # Create a fake playlist with just this video to get metadata
            video_info = self._get_video_info(video_id)
            
            # Extract transcript
            transcript_extractor = TranscriptExtractor(use_web_api=self.use_web_api)
            transcript = transcript_extractor.extract_video_transcript(video_id, video_info['title'])
            
            if not transcript:
                return {
                    "success": False,
                    "error": "Failed to extract transcript",
                    "video_id": video_id
                }
            
            # Create output directory based on video title
            video_title_clean = sanitize_filename(video_info['title'])
            output_dir = Path(base_output_dir) / video_title_clean
            output_dir.mkdir(parents=True, exist_ok=True)
            
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
                
                # Detailed segments
                "segments": [
                    {
                        "start": segment.start,
                        "duration": segment.duration,
                        "text": segment.text,
                        "timestamp": f"{int(segment.start // 60):02d}:{int(segment.start % 60):02d}"
                    }
                    for segment in transcript.segments
                ],
                
                # Metadata
                "extraction_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "processing_type": "single_video"
            }
            
            # Save transcript file
            filename = f"{video_title_clean}_{video_id}.json"
            filepath = output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(video_data, f, indent=2, ensure_ascii=False)
            
            total_time = time.time() - start_time
            
            print(f"✅ SUCCESS!")
            print(f"📹 Video: {video_info['title']}")
            print(f"🎭 Channel: {video_info.get('channel_title', 'Unknown')}")
            print(f"🌍 Language: {transcript.language}")
            print(f"📊 Segments: {len(transcript.segments)}")
            print(f"📝 Words: {video_data['transcript']['word_count']:,}")
            print(f"⏱️  Processing Time: {total_time:.2f}s")
            print(f"📁 Output Directory: {output_dir}")
            print(f"📄 File: {filename}")
            
            return {
                "success": True,
                "video_id": video_id,
                "video_title": video_info['title'],
                "output_directory": str(output_dir),
                "filename": filename,
                "word_count": video_data['transcript']['word_count'],
                "segments": len(transcript.segments),
                "processing_time": total_time
            }
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            return {
                "success": False,
                "error": str(e),
                "video_id": video_id
            }
    
    def _get_video_info(self, video_id: str) -> dict:
        """Get video information using YouTube API."""
        try:
            # Try to get video info using the web transcript API first
            if self.use_web_api:
                web_extractor = WebTranscriptExtractor(self.transcript_api_token)
                # Make a request to get video info
                response = web_extractor._make_api_request([video_id])
                if response and len(response) > 0:
                    video_data = response[0]
                    return {
                        "title": video_data.get('title', f'Video {video_id}'),
                        "channel_title": video_data.get('author', 'Unknown'),
                        "description": video_data.get('microformat', {}).get('playerMicroformatRenderer', {}).get('description', {}).get('simpleText', ''),
                        "view_count": video_data.get('microformat', {}).get('playerMicroformatRenderer', {}).get('viewCount'),
                        "published_at": None,  # Would need additional API call
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
    
    def process_url(self, url: str, output_dir: str = "data") -> dict:
        """Process any YouTube URL (playlist or video)."""
        try:
            url_type, url_id = self.identify_url_type(url)
            
            print(f"🎯 Detected: {url_type.upper()} ({url_id})")
            print()
            
            if url_type == "playlist":
                return self.process_playlist(url, output_dir)
            elif url_type == "video":
                return self.process_video(url, output_dir)
            else:
                raise ValueError(f"Unknown URL type: {url_type}")
                
        except Exception as e:
            print(f"❌ Error processing URL: {e}")
            return {"success": False, "error": str(e)}


def main():
    """Main entry point for the YouTube Transcriptor."""
    parser = argparse.ArgumentParser(
        description="YouTube Transcriptor - Extract and organize video transcripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "https://www.youtube.com/playlist?list=PLExample"
  python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  python main.py "dQw4w9WgXcQ"
  python main.py "PLExample" --output-dir "my_transcripts"

Environment Variables:
  YOUTUBE_API_KEY       - Required YouTube Data API v3 key
  TRANSCRIPT_API_TOKEN  - Optional youtube-transcript.io API token (recommended)
        """
    )
    
    parser.add_argument(
        "url",
        help="YouTube playlist URL, video URL, or ID"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        default="data",
        help="Output directory for transcript files (default: data)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Print header
    print("🎬 YouTube Transcriptor")
    print("=" * 50)
    
    try:
        # Initialize processor
        processor = YouTubeProcessor()
        
        # Process URL
        results = processor.process_url(args.url, args.output_dir)
        
        print()
        print("=" * 50)
        
        if results["success"]:
            print("🎉 Processing completed successfully!")
            
            if "output_directory" in results:
                print(f"📁 Check your files in: {results['output_directory']}")
            
            # Show next steps
            print()
            print("💡 What you can do next:")
            print("1. Browse the generated JSON files")
            print("2. Search transcripts using: youtube-transcriptor search 'query' --json-file <file>")
            print("3. Process more playlists or videos")
            
        else:
            print("❌ Processing failed!")
            if "error" in results:
                print(f"Error: {results['error']}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 