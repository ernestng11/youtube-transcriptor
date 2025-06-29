"""YouTube Data API client for playlist and video operations."""

import time
import logging
from typing import Optional, List, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ..config.settings import settings

logger = logging.getLogger(__name__)


class YouTubeClient:
    """Client for interacting with YouTube Data API v3."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize YouTube client with API key."""
        self.api_key = api_key or settings.youtube_api_key
        if not self.api_key:
            raise ValueError("YouTube API key is required")
        
        self.service = build(
            settings.youtube_api_service_name,
            settings.youtube_api_version,
            developerKey=self.api_key
        )
    
    def _make_request_with_retry(self, request) -> Optional[Dict[str, Any]]:
        """Make API request with retry logic."""
        for attempt in range(settings.max_retries):
            try:
                return request.execute()
            except HttpError as e:
                if e.resp.status == 429:  # Rate limit exceeded
                    wait_time = settings.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                elif e.resp.status == 403:  # Quota exceeded
                    logger.error("API quota exceeded")
                    raise
                else:
                    logger.error(f"HTTP error: {e}")
                    if attempt == settings.max_retries - 1:
                        raise
                    time.sleep(settings.retry_delay)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if attempt == settings.max_retries - 1:
                    raise
                time.sleep(settings.retry_delay)
        
        return None
    
    def get_playlist_info(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """Get playlist metadata."""
        try:
            request = self.service.playlists().list(
                part="snippet,status,contentDetails",
                id=playlist_id
            )
            response = self._make_request_with_retry(request)
            
            if response and 'items' in response and response['items']:
                return response['items'][0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting playlist info: {e}")
            return None
    
    def get_playlist_videos(self, playlist_id: str) -> List[str]:
        """Get all video IDs from a playlist."""
        video_ids = []
        next_page_token = None
        
        try:
            while True:
                request = self.service.playlistItems().list(
                    part="contentDetails",
                    playlistId=playlist_id,
                    maxResults=settings.max_results_per_request,
                    pageToken=next_page_token
                )
                
                response = self._make_request_with_retry(request)
                if not response:
                    break
                
                for item in response.get('items', []):
                    video_id = item['contentDetails']['videoId']
                    video_ids.append(video_id)
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
        except Exception as e:
            logger.error(f"Error getting playlist videos: {e}")
        
        return video_ids
    
    def get_videos_info(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """Get detailed information for multiple videos."""
        videos_info = []
        
        # YouTube API allows up to 50 video IDs per request
        batch_size = 50
        
        try:
            for i in range(0, len(video_ids), batch_size):
                batch_ids = video_ids[i:i + batch_size]
                
                request = self.service.videos().list(
                    part="snippet,contentDetails,statistics,status",
                    id=','.join(batch_ids)
                )
                
                response = self._make_request_with_retry(request)
                if response and 'items' in response:
                    videos_info.extend(response['items'])
                    
        except Exception as e:
            logger.error(f"Error getting videos info: {e}")
        
        return videos_info
    
    def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get channel information."""
        try:
            request = self.service.channels().list(
                part="snippet,statistics",
                id=channel_id
            )
            
            response = self._make_request_with_retry(request)
            if response and 'items' in response and response['items']:
                return response['items'][0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return None 