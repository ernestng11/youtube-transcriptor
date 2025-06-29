"""
Comprehensive YouTube playlist transcription pipeline.
Extracts playlist videos, transcripts, and saves organized aggregated transcripts.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .playlist_extractor import PlaylistExtractor
from .transcript_extractor import TranscriptExtractor
from .models import PlaylistData, VideoTranscript
from ..utils.helpers import sanitize_filename
from ..config.settings import settings

logger = logging.getLogger(__name__)


class TranscriptionPipeline:
    """Complete pipeline for playlist transcription and file organization."""
    
    def __init__(self, youtube_api_key: Optional[str] = None, use_web_api: bool = True):
        """
        Initialize the transcription pipeline.
        
        Args:
            youtube_api_key: YouTube Data API key
            use_web_api: Whether to use web API for transcripts (recommended)
        """
        self.youtube_api_key = youtube_api_key or settings.youtube_api_key
        self.use_web_api = use_web_api
        
        if not self.youtube_api_key:
            raise ValueError("YouTube API key is required")
        
        self.playlist_extractor = PlaylistExtractor(self.youtube_api_key)
        self.transcript_extractor = TranscriptExtractor(use_web_api=self.use_web_api)
        
        logger.info(f"Pipeline initialized with web API: {self.use_web_api}")
    
    def process_playlist(self, playlist_url: str, base_output_dir: str = "data") -> Dict[str, Any]:
        """
        Complete pipeline: extract playlist, get transcripts, save organized files.
        
        Args:
            playlist_url: YouTube playlist URL or ID
            base_output_dir: Base directory for output files
            
        Returns:
            Processing results with statistics and file paths
        """
        logger.info(f"Starting pipeline for playlist: {playlist_url}")
        
        results = {
            "playlist_url": playlist_url,
            "start_time": datetime.now().isoformat(),
            "success": False,
            "playlist_data": None,
            "output_directory": None,
            "transcripts_processed": 0,
            "transcripts_failed": 0,
            "saved_files": [],
            "errors": []
        }
        
        try:
            # Step 1: Extract playlist data
            logger.info("Step 1: Extracting playlist data...")
            playlist_result = self.playlist_extractor.extract_playlist(playlist_url)
            
            if not playlist_result.success or not playlist_result.playlist_data:
                error_msg = f"Failed to extract playlist: {playlist_result.error_message}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
                return results
            
            playlist_data = playlist_result.playlist_data
            results["playlist_data"] = {
                "title": playlist_data.playlist_info.title,
                "video_count": len(playlist_data.videos),
                "channel": playlist_data.playlist_info.channel_title
            }
            
            logger.info(f"Found {len(playlist_data.videos)} videos in playlist: {playlist_data.playlist_info.title}")
            
            # Step 2: Create output directory
            output_dir = self._create_output_directory(playlist_data, base_output_dir)
            results["output_directory"] = str(output_dir)
            
            # Step 3: Extract transcripts
            logger.info("Step 2: Extracting transcripts...")
            transcripts = self.transcript_extractor.extract_playlist_transcripts(playlist_data)
            
            logger.info(f"Successfully extracted {len(transcripts)} transcripts")
            
            # Step 4: Process and save individual video transcripts
            logger.info("Step 3: Processing and saving individual transcripts...")
            saved_files = self._save_individual_transcripts(
                transcripts, playlist_data, output_dir
            )
            
            results["saved_files"] = saved_files
            results["transcripts_processed"] = len(transcripts)
            results["transcripts_failed"] = len(playlist_data.videos) - len(transcripts)
            
            # Step 5: Create summary file
            summary_file = self._create_summary_file(playlist_data, transcripts, output_dir, results)
            results["saved_files"].append(str(summary_file))
            
            results["success"] = True
            results["end_time"] = datetime.now().isoformat()
            
            logger.info(f"Pipeline completed successfully!")
            logger.info(f"Processed: {results['transcripts_processed']} videos")
            logger.info(f"Failed: {results['transcripts_failed']} videos")
            logger.info(f"Output directory: {output_dir}")
            
            return results
            
        except Exception as e:
            error_msg = f"Pipeline failed: {e}"
            results["errors"].append(error_msg)
            logger.error(error_msg, exc_info=True)
            return results
    
    def _create_output_directory(self, playlist_data: PlaylistData, base_dir: str) -> Path:
        """Create organized output directory structure."""
        # Sanitize playlist title for directory name
        playlist_title = sanitize_filename(playlist_data.playlist_info.title)
        
        # Create directory path
        output_dir = Path(base_dir) / playlist_title
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created output directory: {output_dir}")
        return output_dir
    
    def _save_individual_transcripts(self, transcripts: List[VideoTranscript], 
                                   playlist_data: PlaylistData, output_dir: Path) -> List[str]:
        """Save individual aggregated transcript files for each video."""
        saved_files = []
        
        # Create video metadata lookup
        video_lookup = {video.id: video for video in playlist_data.videos}
        
        for transcript in transcripts:
            try:
                # Get video metadata
                video = video_lookup.get(transcript.video_id)
                if not video:
                    logger.warning(f"Video metadata not found for {transcript.video_id}")
                    continue
                
                # Aggregate transcript segments into continuous text
                aggregated_text = self._aggregate_transcript_text(transcript)
                
                # Create comprehensive video data
                video_data = {
                    "video_id": transcript.video_id,
                    "video_title": transcript.video_title,
                    "video_url": f"https://www.youtube.com/watch?v={transcript.video_id}",
                    "channel_title": video.channel_title,
                    "published_at": video.published_at.isoformat() if video.published_at else None,
                    "duration_seconds": video.duration_seconds,
                    "view_count": video.view_count,
                    "like_count": video.like_count,
                    "description": video.description,
                    
                    # Transcript data
                    "transcript": {
                        "language": transcript.language,
                        "is_auto_generated": transcript.is_auto_generated,
                        "total_segments": len(transcript.segments),
                        "aggregated_text": aggregated_text,
                        "text_length": len(aggregated_text),
                        "word_count": len(aggregated_text.split()) if aggregated_text else 0
                    },
                    
                    # Detailed segments (optional, for reference)
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
                    "extraction_timestamp": datetime.now().isoformat(),
                    "playlist_title": playlist_data.playlist_info.title
                }
                
                # Create filename (sanitized video title + video ID)
                video_title_clean = sanitize_filename(transcript.video_title)
                filename = f"{video_title_clean}_{transcript.video_id}.json"
                filepath = output_dir / filename
                
                # Save file
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(video_data, f, indent=2, ensure_ascii=False)
                
                saved_files.append(str(filepath))
                logger.debug(f"Saved transcript: {filename}")
                
            except Exception as e:
                error_msg = f"Failed to save transcript for {transcript.video_id}: {e}"
                logger.error(error_msg)
                continue
        
        logger.info(f"Saved {len(saved_files)} individual transcript files")
        return saved_files
    
    def _aggregate_transcript_text(self, transcript: VideoTranscript) -> str:
        """Aggregate transcript segments into continuous text."""
        if not transcript.segments:
            return ""
        
        # Join all segment texts with spaces
        aggregated = " ".join(segment.text for segment in transcript.segments if segment.text.strip())
        
        # Clean up extra whitespace
        aggregated = " ".join(aggregated.split())
        
        return aggregated
    
    def _create_summary_file(self, playlist_data: PlaylistData, transcripts: List[VideoTranscript], 
                           output_dir: Path, results: Dict[str, Any]) -> Path:
        """Create a summary file for the entire playlist."""
        
        # Calculate statistics
        total_segments = sum(len(t.segments) for t in transcripts)
        total_words = sum(len(self._aggregate_transcript_text(t).split()) for t in transcripts)
        total_chars = sum(len(self._aggregate_transcript_text(t)) for t in transcripts)
        
        # Calculate total duration from video data
        total_duration = sum(video.duration_seconds or 0 for video in playlist_data.videos)
        
        summary_data = {
            "playlist_info": {
                "title": playlist_data.playlist_info.title,
                "channel_title": playlist_data.playlist_info.channel_title,
                "url": f"https://www.youtube.com/playlist?list={playlist_data.playlist_info.id}",
                "total_videos": len(playlist_data.videos),
                "total_duration_seconds": total_duration,
                "total_duration_formatted": self._format_duration(total_duration)
            },
            
            "transcript_statistics": {
                "videos_with_transcripts": len(transcripts),
                "videos_without_transcripts": len(playlist_data.videos) - len(transcripts),
                "success_rate": f"{len(transcripts)/len(playlist_data.videos)*100:.1f}%",
                "total_segments": total_segments,
                "total_words": total_words,
                "total_characters": total_chars,
                "average_words_per_video": int(total_words / len(transcripts)) if transcripts else 0
            },
            
            "processing_info": {
                "extraction_timestamp": datetime.now().isoformat(),
                "web_api_used": self.use_web_api,
                "processing_time": results.get("end_time", ""),
                "output_directory": str(output_dir)
            },
            
            "video_list": [
                {
                    "video_id": video.id,
                    "title": video.title,
                    "duration_seconds": video.duration_seconds,
                    "has_transcript": any(t.video_id == video.id for t in transcripts),
                    "filename": f"{sanitize_filename(video.title)}_{video.id}.json" if any(t.video_id == video.id for t in transcripts) else None
                }
                for video in playlist_data.videos
            ]
        }
        
        # Save summary file
        summary_filename = f"_playlist_summary_{sanitize_filename(playlist_data.playlist_info.title)}.json"
        summary_filepath = output_dir / summary_filename
        
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created playlist summary: {summary_filename}")
        return summary_filepath
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to HH:MM:SS."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about the pipeline components."""
        return {
            "youtube_api_configured": bool(self.youtube_api_key),
            "web_api_enabled": self.use_web_api,
            "web_api_token_configured": bool(settings.transcript_api_token),
            "pipeline_components": {
                "playlist_extractor": "PlaylistExtractor",
                "transcript_extractor": "TranscriptExtractor",
                "web_api_integration": self.use_web_api
            }
        } 