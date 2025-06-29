"""Data models for YouTube playlist and video information."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class ChannelInfo(BaseModel):
    """Information about a YouTube channel."""
    
    id: str
    title: str
    description: Optional[str] = None
    custom_url: Optional[str] = None
    published_at: Optional[datetime] = None
    thumbnail_url: Optional[str] = None
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    view_count: Optional[int] = None


class VideoThumbnail(BaseModel):
    """Video thumbnail information."""
    
    url: str
    width: int
    height: int


class VideoInfo(BaseModel):
    """Information about a YouTube video."""
    
    id: str
    title: str
    description: Optional[str] = None
    channel_id: str
    channel_title: str
    published_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    duration_iso: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    thumbnail_default: Optional[VideoThumbnail] = None
    thumbnail_medium: Optional[VideoThumbnail] = None
    thumbnail_high: Optional[VideoThumbnail] = None
    thumbnail_standard: Optional[VideoThumbnail] = None
    thumbnail_maxres: Optional[VideoThumbnail] = None
    tags: Optional[List[str]] = None
    category_id: Optional[str] = None
    default_language: Optional[str] = None
    privacy_status: Optional[str] = None
    
    @validator('duration_seconds', pre=True, always=True)
    def parse_duration(cls, v, values):
        """Parse ISO 8601 duration to seconds."""
        if v is not None:
            return v
        
        duration_iso = values.get('duration_iso')
        if duration_iso:
            return cls._parse_iso_duration(duration_iso)
        return None
    
    @staticmethod
    def _parse_iso_duration(duration: str) -> int:
        """Parse ISO 8601 duration (PT1H2M3S) to seconds."""
        import re
        
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration)
        
        if not match:
            return 0
            
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds


class PlaylistInfo(BaseModel):
    """Information about a YouTube playlist."""
    
    id: str
    title: str
    description: Optional[str] = None
    channel_id: str
    channel_title: str
    published_at: Optional[datetime] = None
    privacy_status: Optional[str] = None
    video_count: Optional[int] = None
    thumbnail_default: Optional[VideoThumbnail] = None
    thumbnail_medium: Optional[VideoThumbnail] = None
    thumbnail_high: Optional[VideoThumbnail] = None
    thumbnail_standard: Optional[VideoThumbnail] = None
    thumbnail_maxres: Optional[VideoThumbnail] = None
    tags: Optional[List[str]] = None
    default_language: Optional[str] = None


class PlaylistData(BaseModel):
    """Complete playlist data including all videos."""
    
    playlist_info: PlaylistInfo
    videos: List[VideoInfo]
    total_duration_seconds: Optional[int] = None
    extracted_at: datetime = Field(default_factory=datetime.now)
    
    @validator('total_duration_seconds', pre=True, always=True)
    def calculate_total_duration(cls, v, values):
        """Calculate total duration from all videos."""
        if v is not None:
            return v
            
        videos = values.get('videos', [])
        total = 0
        for video in videos:
            if video.duration_seconds:
                total += video.duration_seconds
        
        return total if total > 0 else None


class ExtractionResult(BaseModel):
    """Result of playlist extraction operation."""
    
    success: bool
    playlist_data: Optional[PlaylistData] = None
    error_message: Optional[str] = None
    videos_processed: int = 0
    videos_failed: int = 0
    extraction_time_seconds: Optional[float] = None


class TranscriptSegment(BaseModel):
    """Individual transcript segment with timing."""
    
    text: str
    start: float  # seconds
    duration: float  # seconds
    
    @property
    def end(self) -> float:
        """Calculate end time."""
        return self.start + self.duration


class VideoTranscript(BaseModel):
    """Complete transcript for a video."""
    
    video_id: str
    video_title: str
    language: str
    is_auto_generated: bool
    segments: List[TranscriptSegment]
    extracted_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def full_text(self) -> str:
        """Get combined text from all segments."""
        return " ".join(segment.text for segment in self.segments)
    
    @property
    def word_count(self) -> int:
        """Count words in transcript."""
        return len(self.full_text.split())


class SearchResult(BaseModel):
    """Search result with context."""
    
    video_id: str
    video_title: str
    segment: TranscriptSegment
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    match_position: int  # character position in segment text


class PlaylistSearchResults(BaseModel):
    """Search results across entire playlist."""
    
    query: str
    playlist_title: str
    total_results: int
    results: List[SearchResult]
    searched_videos: int
    videos_with_transcripts: int
    search_time_seconds: float 