"""Transcript extraction and search functionality."""

import time
import logging
import re
from typing import List, Optional, Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

from .models import (
    TranscriptSegment, VideoTranscript, SearchResult, 
    PlaylistSearchResults, PlaylistData
)
from .web_transcript_extractor import WebTranscriptExtractor
from ..config.settings import settings

logger = logging.getLogger(__name__)


class TranscriptExtractor:
    """Extract and search transcripts from YouTube videos."""
    
    def __init__(self, use_web_api: bool = True):
        """
        Initialize transcript extractor.
        
        Args:
            use_web_api: Whether to use youtube-transcript.io web API as primary method
        """
        self.api = YouTubeTranscriptApi()
        self.use_web_api = use_web_api and settings.transcript_api_token
        self.web_extractor = None
        
        if self.use_web_api:
            self.web_extractor = WebTranscriptExtractor(settings.transcript_api_token)
            logger.info("Web transcript API enabled (youtube-transcript.io)")
        else:
            logger.info("Using YouTube Transcript API only")
    
    def extract_video_transcript(self, video_id: str, video_title: str = "") -> Optional[VideoTranscript]:
        """Extract transcript for a single video."""
        # Try web API first if available
        if self.use_web_api and self.web_extractor:
            try:
                transcript = self.web_extractor.extract_video_transcript(
                    video_id, video_title, settings.transcript_country_code
                )
                if transcript:
                    logger.debug(f"Successfully extracted transcript via web API for {video_id}")
                    return transcript
                else:
                    logger.debug(f"Web API failed for {video_id}, trying YouTube API")
            except Exception as e:
                logger.warning(f"Web API error for {video_id}: {e}, falling back to YouTube API")
        
        # Fallback to YouTube Transcript API
        try:
            # Get transcript using the simpler API
            raw_transcript = self.api.get_transcript(video_id, languages=['en'])
            is_auto_generated = True  # Most transcripts are auto-generated
            language = 'en'
            
            # Process segments
            segments = self._process_transcript_segments(raw_transcript)
            
            return VideoTranscript(
                video_id=video_id,
                video_title=video_title,
                language=language,
                is_auto_generated=is_auto_generated,
                segments=segments
            )
            
        except TranscriptsDisabled:
            logger.warning(f"Transcripts disabled for video {video_id}")
        except VideoUnavailable:
            logger.warning(f"Video {video_id} is unavailable")
        except Exception as e:
            logger.error(f"Error extracting transcript for video {video_id}: {e}")
        
        return None
    
    def extract_playlist_transcripts(self, playlist_data: PlaylistData) -> List[VideoTranscript]:
        """Extract transcripts for all videos in a playlist."""
        # Use batch processing with web API if available
        if self.use_web_api and self.web_extractor:
            return self._extract_playlist_transcripts_batch(playlist_data)
        else:
            return self._extract_playlist_transcripts_sequential(playlist_data)
    
    def _extract_playlist_transcripts_batch(self, playlist_data: PlaylistData) -> List[VideoTranscript]:
        """Extract transcripts using web API batch processing."""
        logger.info(f"Extracting transcripts for {len(playlist_data.videos)} videos using batch processing")
        
        # Prepare video data
        video_ids = [video.id for video in playlist_data.videos]
        video_titles = {video.id: video.title for video in playlist_data.videos}
        
        # Use web API batch extraction
        if self.web_extractor:
            transcripts = self.web_extractor.extract_batch_transcripts(
                video_ids, video_titles, settings.transcript_country_code
            )
        else:
            transcripts = []
        
        # For videos that failed with web API, try individual YouTube API extraction
        successful_video_ids = {t.video_id for t in transcripts}
        failed_videos = [v for v in playlist_data.videos if v.id not in successful_video_ids]
        
        if failed_videos:
            logger.info(f"Retrying {len(failed_videos)} failed videos with YouTube API")
            for video in failed_videos:
                transcript = self._extract_with_youtube_api(video.id, video.title)
                if transcript:
                    transcripts.append(transcript)
        
        logger.info(f"Successfully extracted {len(transcripts)} transcripts")
        return transcripts
    
    def _extract_playlist_transcripts_sequential(self, playlist_data: PlaylistData) -> List[VideoTranscript]:
        """Extract transcripts sequentially (fallback method)."""
        transcripts = []
        
        logger.info(f"Extracting transcripts for {len(playlist_data.videos)} videos sequentially")
        
        for video in playlist_data.videos:
            transcript = self.extract_video_transcript(video.id, video.title)
            if transcript:
                transcripts.append(transcript)
                logger.debug(f"Successfully extracted transcript for {video.title}")
            else:
                logger.debug(f"No transcript available for {video.title}")
        
        logger.info(f"Successfully extracted {len(transcripts)} transcripts")
        return transcripts
    
    def _extract_with_youtube_api(self, video_id: str, video_title: str = "") -> Optional[VideoTranscript]:
        """Extract transcript using only YouTube API (fallback method)."""
        try:
            # Get transcript using the simpler API
            raw_transcript = self.api.get_transcript(video_id, languages=['en'])
            is_auto_generated = True  # Most transcripts are auto-generated
            language = 'en'
            
            # Process segments
            segments = self._process_transcript_segments(raw_transcript)
            
            return VideoTranscript(
                video_id=video_id,
                video_title=video_title,
                language=language,
                is_auto_generated=is_auto_generated,
                segments=segments
            )
            
        except TranscriptsDisabled:
            logger.warning(f"Transcripts disabled for video {video_id}")
        except VideoUnavailable:
            logger.warning(f"Video {video_id} is unavailable")
        except Exception as e:
            logger.error(f"Error extracting transcript for video {video_id}: {e}")
        
        return None
    
    def search_transcripts(self, transcripts: List[VideoTranscript], query: str, 
                          case_sensitive: bool = False) -> PlaylistSearchResults:
        """Search for text across all transcripts."""
        start_time = time.time()
        results = []
        
        # Prepare search query
        search_query = query if case_sensitive else query.lower()
        
        for transcript in transcripts:
            video_results = self._search_video_transcript(transcript, search_query, case_sensitive)
            results.extend(video_results)
        
        search_time = time.time() - start_time
        
        return PlaylistSearchResults(
            query=query,
            playlist_title="Search Results",  # Will be updated by caller
            total_results=len(results),
            results=results,
            searched_videos=len(transcripts),
            videos_with_transcripts=len(transcripts),
            search_time_seconds=search_time
        )
    
    def _search_video_transcript(self, transcript: VideoTranscript, query: str, 
                               case_sensitive: bool) -> List[SearchResult]:
        """Search within a single video transcript."""
        results = []
        
        for i, segment in enumerate(transcript.segments):
            text = segment.text if case_sensitive else segment.text.lower()
            
            # Find all occurrences in this segment
            start_pos = 0
            while True:
                pos = text.find(query, start_pos)
                if pos == -1:
                    break
                
                # Get context
                context_before = self._get_context_before(transcript.segments, i)
                context_after = self._get_context_after(transcript.segments, i)
                
                results.append(SearchResult(
                    video_id=transcript.video_id,
                    video_title=transcript.video_title,
                    segment=segment,
                    context_before=context_before,
                    context_after=context_after,
                    match_position=pos
                ))
                
                start_pos = pos + 1
        
        return results
    
    def _process_transcript_segments(self, raw_transcript: List[Dict[str, Any]]) -> List[TranscriptSegment]:
        """Process raw transcript data into structured segments."""
        segments = []
        
        for item in raw_transcript:
            # Clean up the text
            text = self._clean_transcript_text(item.get('text', ''))
            if text.strip():  # Only add non-empty segments
                segments.append(TranscriptSegment(
                    text=text,
                    start=float(item.get('start', 0)),
                    duration=float(item.get('duration', 0))
                ))
        
        return segments
    
    def _clean_transcript_text(self, text: str) -> str:
        """Clean up transcript text."""
        # Remove common auto-generated artifacts
        text = re.sub(r'\[.*?\]', '', text)  # Remove [Music], [Applause], etc.
        text = re.sub(r'\(.*?\)', '', text)  # Remove (laughs), etc.
        text = re.sub(r'\s+', ' ', text)     # Normalize whitespace
        text = text.strip()
        
        return text
    
    def _get_context_before(self, segments: List[TranscriptSegment], current_index: int, 
                          context_length: int = 50) -> Optional[str]:
        """Get context before the current segment."""
        if current_index == 0:
            return None
        
        context_segments = segments[max(0, current_index - 2):current_index]
        context_text = " ".join(seg.text for seg in context_segments)
        
        if len(context_text) > context_length:
            context_text = "..." + context_text[-context_length:]
        
        return context_text if context_text else None
    
    def _get_context_after(self, segments: List[TranscriptSegment], current_index: int, 
                         context_length: int = 50) -> Optional[str]:
        """Get context after the current segment."""
        if current_index >= len(segments) - 1:
            return None
        
        context_segments = segments[current_index + 1:current_index + 3]
        context_text = " ".join(seg.text for seg in context_segments)
        
        if len(context_text) > context_length:
            context_text = context_text[:context_length] + "..."
        
        return context_text if context_text else None 