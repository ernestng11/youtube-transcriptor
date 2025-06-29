"""
Web-based transcript extraction using youtube-transcript.io API.
This provides an alternative to the blocked YouTube transcript API.
"""

import time
import logging
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from .models import TranscriptSegment, VideoTranscript
from ..config.settings import settings

logger = logging.getLogger(__name__)


class WebTranscriptExtractor:
    """Extract transcripts using youtube-transcript.io API."""
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize web transcript extractor.
        
        Args:
            api_token: API token from youtube-transcript.io profile
        """
        self.api_token = api_token
        self.base_url = "https://www.youtube-transcript.io/api"
        self.rate_limit_requests = 5  # 5 requests per 10 seconds
        self.rate_limit_window = 10   # seconds
        self.request_times = []  # Track request timestamps for rate limiting
        
        if not self.api_token:
            logger.warning("No API token provided for youtube-transcript.io")
    
    def extract_video_transcript(self, video_id: str, video_title: str = "", 
                               country_code: str = "us") -> Optional[VideoTranscript]:
        """
        Extract transcript for a single video.
        
        Args:
            video_id: YouTube video ID
            video_title: Video title for metadata
            country_code: Country code for transcript fetching (default: "us")
            
        Returns:
            VideoTranscript object or None if extraction fails
        """
        if not self.api_token:
            logger.error("API token required for youtube-transcript.io")
            return None
        
        try:
            # Rate limiting
            self._wait_for_rate_limit()
            
            # Make API request
            response = self._make_api_request([video_id], country_code)
            
            if response:
                # Find the video in the response list
                video_data = None
                for item in response:
                    if item.get('id') == video_id:
                        video_data = item
                        break
                
                if video_data:
                    # Extract transcript from tracks
                    tracks = video_data.get('tracks', [])
                    if tracks and len(tracks) > 0:
                        track = tracks[0]  # Use first available track
                        transcript_segments = track.get('transcript', [])
                        language = track.get('language', 'en')
                        
                        segments = self._parse_transcript_segments(transcript_segments)
                        
                        return VideoTranscript(
                            video_id=video_id,
                            video_title=video_title or video_data.get('title', f"Video {video_id}"),
                            language=language,
                            is_auto_generated='auto-generated' in language.lower(),
                            segments=segments
                        )
                    else:
                        logger.warning(f"No transcript tracks found for video {video_id}")
                else:
                    logger.warning(f"Video {video_id} not found in API response")
            
        except Exception as e:
            logger.error(f"Error extracting transcript for {video_id}: {e}")
        
        return None
    
    def extract_batch_transcripts(self, video_ids: List[str], video_titles: Optional[Dict[str, str]] = None, 
                                country_code: str = "us") -> List[VideoTranscript]:
        """
        Extract transcripts for multiple videos in batches.
        
        Args:
            video_ids: List of YouTube video IDs
            video_titles: Optional mapping of video_id -> title
            country_code: Country code for transcript fetching
            
        Returns:
            List of VideoTranscript objects
        """
        if not self.api_token:
            logger.error("API token required for youtube-transcript.io")
            return []
        
        video_titles = video_titles or {}
        transcripts = []
        batch_size = 50  # API limit
        
        logger.info(f"Extracting transcripts for {len(video_ids)} videos in batches of {batch_size}")
        
        for i in range(0, len(video_ids), batch_size):
            batch = video_ids[i:i + batch_size]
            
            try:
                # Rate limiting
                self._wait_for_rate_limit()
                
                # Make API request for batch
                response = self._make_api_request(batch, country_code)
                
                if response:
                    # Process each video in the response
                    for video_data in response:
                        video_id = video_data.get('id')
                        if not video_id:
                            continue
                        
                        # Extract transcript from tracks
                        tracks = video_data.get('tracks', [])
                        if tracks and len(tracks) > 0:
                            track = tracks[0]  # Use first available track
                            transcript_segments = track.get('transcript', [])
                            language = track.get('language', 'en')
                            
                            segments = self._parse_transcript_segments(transcript_segments)
                            
                            transcript = VideoTranscript(
                                video_id=video_id,
                                video_title=video_titles.get(video_id, video_data.get('title', f"Video {video_id}")),
                                language=language,
                                is_auto_generated='auto-generated' in language.lower(),
                                segments=segments
                            )
                            transcripts.append(transcript)
                            logger.debug(f"Successfully extracted transcript for {video_id}")
                        else:
                            logger.warning(f"No transcript tracks found for {video_id}")
                
                logger.info(f"Processed batch {i//batch_size + 1}, total transcripts: {len(transcripts)}")
                
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                continue
        
        logger.info(f"Successfully extracted {len(transcripts)} transcripts")
        return transcripts
    
    def _make_api_request(self, video_ids: List[str], country_code: str = "us") -> Optional[List[Dict[str, Any]]]:
        """
        Make API request to youtube-transcript.io.
        
        Args:
            video_ids: List of video IDs to fetch
            country_code: Country code for transcript fetching
            
        Returns:
            API response data (list of video objects) or None if request fails
        """
        url = f"{self.base_url}/transcripts"
        
        headers = {
            "Authorization": f"Basic {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "ids": video_ids,
            "countryCode": country_code
        }
        
        try:
            # Record request time for rate limiting
            self.request_times.append(time.time())
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
                else:
                    logger.error(f"Unexpected response format: expected list, got {type(data)}")
                    return None
            elif response.status_code == 429:
                # Rate limit exceeded
                retry_after = int(response.headers.get('Retry-After', 10))
                logger.warning(f"Rate limit exceeded, waiting {retry_after} seconds")
                time.sleep(retry_after)
                # Retry the request
                return self._make_api_request(video_ids, country_code)
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during API request: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during API request: {e}")
            return None
    
    def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits (5 requests per 10 seconds)."""
        current_time = time.time()
        
        # Remove old request times outside the window
        self.request_times = [t for t in self.request_times if current_time - t < self.rate_limit_window]
        
        # If we're at the limit, wait
        if len(self.request_times) >= self.rate_limit_requests:
            sleep_time = self.rate_limit_window - (current_time - self.request_times[0]) + 0.1
            if sleep_time > 0:
                logger.info(f"Rate limiting: waiting {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
    
    def _parse_transcript_segments(self, transcript_data: List[Dict[str, Any]]) -> List[TranscriptSegment]:
        """
        Parse transcript data into TranscriptSegment objects.
        
        Args:
            transcript_data: Raw transcript data from API
            
        Returns:
            List of TranscriptSegment objects
        """
        segments = []
        
        for item in transcript_data:
            try:
                # Handle the API format: text, start, dur (as strings)
                text = item.get('text', '').strip()
                start = float(item.get('start', '0'))
                # API uses 'dur' field name, not 'duration'
                duration = float(item.get('dur', item.get('duration', '0')))
                
                if text:  # Only add non-empty segments
                    segments.append(TranscriptSegment(
                        text=text,
                        start=start,
                        duration=duration
                    ))
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing transcript segment {item}: {e}")
                continue
        
        return segments
    
    def get_usage_info(self) -> Dict[str, Any]:
        """
        Get information about API usage and limits.
        
        Returns:
            Dictionary with usage information
        """
        return {
            "api_provider": "youtube-transcript.io",
            "rate_limit": f"{self.rate_limit_requests} requests per {self.rate_limit_window} seconds",
            "batch_size": 50,
            "recent_requests": len(self.request_times),
            "has_api_token": bool(self.api_token),
            "api_endpoint": f"{self.base_url}/transcripts"
        } 