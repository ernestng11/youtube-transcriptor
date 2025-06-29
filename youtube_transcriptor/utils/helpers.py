"""Helper utility functions."""

import re
from typing import Optional
from urllib.parse import urlparse, parse_qs


def parse_playlist_url(url: str) -> Optional[str]:
    """
    Extract playlist ID from various YouTube URL formats.
    
    Supported formats:
    - https://www.youtube.com/playlist?list=PLxxxxxx
    - https://www.youtube.com/watch?v=xxxxx&list=PLxxxxxx
    - PLxxxxxx (direct playlist ID)
    """
    # If it's already a playlist ID (starts with PL)
    if url.startswith('PL') and len(url) > 10:
        return url
    
    try:
        # Parse the URL
        parsed_url = urlparse(url)
        
        # Extract query parameters
        query_params = parse_qs(parsed_url.query)
        
        # Look for 'list' parameter
        if 'list' in query_params:
            playlist_id = query_params['list'][0]
            if playlist_id.startswith('PL'):
                return playlist_id
    
    except Exception:
        pass
    
    return None


def format_duration(seconds: Optional[int]) -> str:
    """Format duration in seconds to human readable format."""
    if seconds is None:
        return "Unknown"
    
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return f"{hours}h {minutes}m {remaining_seconds}s"


def format_number(number: Optional[int]) -> str:
    """Format large numbers with commas."""
    if number is None:
        return "N/A"
    
    return f"{number:,}"


def truncate_text(text: Optional[str], max_length: int = 100) -> str:
    """Truncate text to specified length with ellipsis."""
    if not text:
        return "N/A"
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def extract_video_id_from_url(url: str) -> Optional[str]:
    """Extract video ID from YouTube video URL."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def is_valid_youtube_url(url: str) -> bool:
    """Check if URL is a valid YouTube URL."""
    youtube_domains = ['youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com']
    
    try:
        parsed_url = urlparse(url)
        return parsed_url.hostname in youtube_domains
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system operations."""
    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove all whitespaces (spaces, tabs, etc.)
    sanitized = re.sub(r'\s+', '', sanitized)
    
    # Remove leading/trailing dots and underscores
    sanitized = sanitized.strip('._')
    
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    return sanitized or "untitled" 