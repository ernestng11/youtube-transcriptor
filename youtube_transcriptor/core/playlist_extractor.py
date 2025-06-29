"""Main playlist extraction logic."""

import logging
import time
from datetime import datetime
from typing import Optional, List
from .youtube_client import YouTubeClient
from .models import (
    PlaylistInfo, VideoInfo, PlaylistData, ExtractionResult,
    VideoThumbnail, ChannelInfo
)
from ..utils.helpers import parse_playlist_url, format_duration
from ..utils.validators import validate_playlist_url

logger = logging.getLogger(__name__)


class PlaylistExtractor:
    """Main class for extracting YouTube playlist data."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize playlist extractor."""
        self.youtube_client = YouTubeClient(api_key)
    
    def extract_playlist(self, playlist_url: str) -> ExtractionResult:
        """Extract complete playlist data."""
        start_time = time.time()
        
        try:
            # Validate and parse playlist URL
            if not validate_playlist_url(playlist_url):
                return ExtractionResult(
                    success=False,
                    error_message=f"Invalid playlist URL: {playlist_url}"
                )
            
            playlist_id = parse_playlist_url(playlist_url)
            if not playlist_id:
                return ExtractionResult(
                    success=False,
                    error_message=f"Could not extract playlist ID from URL: {playlist_url}"
                )
            
            logger.info(f"Extracting playlist: {playlist_id}")
            
            # Get playlist info
            playlist_raw = self.youtube_client.get_playlist_info(playlist_id)
            if not playlist_raw:
                return ExtractionResult(
                    success=False,
                    error_message=f"Playlist not found or not accessible: {playlist_id}"
                )
            
            # Get all video IDs from playlist
            video_ids = self.youtube_client.get_playlist_videos(playlist_id)
            if not video_ids:
                return ExtractionResult(
                    success=False,
                    error_message=f"No videos found in playlist: {playlist_id}"
                )
            
            logger.info(f"Found {len(video_ids)} videos in playlist")
            
            # Get detailed video information
            videos_raw = self.youtube_client.get_videos_info(video_ids)
            
            # Process the data
            playlist_info = self._process_playlist_info(playlist_raw)
            videos_info = self._process_videos_info(videos_raw)
            
            # Create playlist data
            playlist_data = PlaylistData(
                playlist_info=playlist_info,
                videos=videos_info
            )
            
            extraction_time = time.time() - start_time
            
            return ExtractionResult(
                success=True,
                playlist_data=playlist_data,
                videos_processed=len(videos_info),
                videos_failed=len(video_ids) - len(videos_info),
                extraction_time_seconds=extraction_time
            )
            
        except Exception as e:
            logger.error(f"Error extracting playlist: {e}")
            extraction_time = time.time() - start_time
            
            return ExtractionResult(
                success=False,
                error_message=str(e),
                extraction_time_seconds=extraction_time
            )
    
    def _process_playlist_info(self, playlist_raw: dict) -> PlaylistInfo:
        """Process raw playlist data into structured format."""
        snippet = playlist_raw.get('snippet', {})
        status = playlist_raw.get('status', {})
        content_details = playlist_raw.get('contentDetails', {})
        
        thumbnails = snippet.get('thumbnails', {})
        
        return PlaylistInfo(
            id=playlist_raw['id'],
            title=snippet.get('title', ''),
            description=snippet.get('description'),
            channel_id=snippet.get('channelId', ''),
            channel_title=snippet.get('channelTitle', ''),
            published_at=self._parse_datetime(snippet.get('publishedAt')),
            privacy_status=status.get('privacyStatus'),
            video_count=content_details.get('itemCount'),
            thumbnail_default=self._process_thumbnail(thumbnails.get('default')),
            thumbnail_medium=self._process_thumbnail(thumbnails.get('medium')),
            thumbnail_high=self._process_thumbnail(thumbnails.get('high')),
            thumbnail_standard=self._process_thumbnail(thumbnails.get('standard')),
            thumbnail_maxres=self._process_thumbnail(thumbnails.get('maxres')),
            tags=snippet.get('tags'),
            default_language=snippet.get('defaultLanguage')
        )
    
    def _process_videos_info(self, videos_raw: List[dict]) -> List[VideoInfo]:
        """Process raw videos data into structured format."""
        videos_info = []
        
        for video_raw in videos_raw:
            try:
                video_info = self._process_single_video_info(video_raw)
                videos_info.append(video_info)
            except Exception as e:
                logger.warning(f"Error processing video {video_raw.get('id', 'unknown')}: {e}")
                continue
        
        return videos_info
    
    def _process_single_video_info(self, video_raw: dict) -> VideoInfo:
        """Process single video raw data into structured format."""
        snippet = video_raw.get('snippet', {})
        content_details = video_raw.get('contentDetails', {})
        statistics = video_raw.get('statistics', {})
        status = video_raw.get('status', {})
        
        thumbnails = snippet.get('thumbnails', {})
        
        return VideoInfo(
            id=video_raw['id'],
            title=snippet.get('title', ''),
            description=snippet.get('description'),
            channel_id=snippet.get('channelId', ''),
            channel_title=snippet.get('channelTitle', ''),
            published_at=self._parse_datetime(snippet.get('publishedAt')),
            duration_iso=content_details.get('duration'),
            view_count=self._parse_int(statistics.get('viewCount')),
            like_count=self._parse_int(statistics.get('likeCount')),
            comment_count=self._parse_int(statistics.get('commentCount')),
            thumbnail_default=self._process_thumbnail(thumbnails.get('default')),
            thumbnail_medium=self._process_thumbnail(thumbnails.get('medium')),
            thumbnail_high=self._process_thumbnail(thumbnails.get('high')),
            thumbnail_standard=self._process_thumbnail(thumbnails.get('standard')),
            thumbnail_maxres=self._process_thumbnail(thumbnails.get('maxres')),
            tags=snippet.get('tags'),
            category_id=snippet.get('categoryId'),
            default_language=snippet.get('defaultLanguage'),
            privacy_status=status.get('privacyStatus')
        )
    
    def _process_thumbnail(self, thumbnail_raw: Optional[dict]) -> Optional[VideoThumbnail]:
        """Process thumbnail data."""
        if not thumbnail_raw:
            return None
        
        return VideoThumbnail(
            url=thumbnail_raw['url'],
            width=thumbnail_raw['width'],
            height=thumbnail_raw['height']
        )
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string."""
        if not date_str:
            return None
        
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Could not parse datetime: {date_str}")
            return None
    
    def _parse_int(self, value: Optional[str]) -> Optional[int]:
        """Parse string to integer."""
        if not value:
            return None
        
        try:
            return int(value)
        except ValueError:
            return None 