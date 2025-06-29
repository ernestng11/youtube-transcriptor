"""Input validation utilities."""

import re
from typing import Optional
from urllib.parse import urlparse


def validate_playlist_url(url: Optional[str]) -> bool:
    """
    Validate if the provided URL is a valid YouTube playlist URL or ID.
    
    Args:
        url: The URL or playlist ID to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    
    # Check if it's a direct playlist ID
    if url.startswith('PL') and len(url) >= 16:
        # Playlist IDs are typically 34 characters long and start with 'PL'
        return bool(re.match(r'^PL[a-zA-Z0-9_-]{16,}$', url))
    
    # Check if it's a valid YouTube URL
    try:
        parsed_url = urlparse(url)
        
        # Must be a YouTube domain
        valid_domains = ['youtube.com', 'www.youtube.com', 'm.youtube.com']
        if parsed_url.hostname not in valid_domains:
            return False
        
        # Must have a list parameter in query string
        if 'list=' not in url:
            return False
        
        return True
        
    except Exception:
        return False


def validate_api_key(api_key: Optional[str]) -> bool:
    """
    Validate YouTube Data API key format.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        bool: True if format looks valid, False otherwise
    """
    if not api_key or not isinstance(api_key, str):
        return False
    
    api_key = api_key.strip()
    
    # Basic format validation for Google API keys
    # They are typically 39 characters long and contain alphanumeric characters and some symbols
    if len(api_key) < 30 or len(api_key) > 50:
        return False
    
    # Should contain only valid characters
    if not re.match(r'^[a-zA-Z0-9_-]+$', api_key):
        return False
    
    return True


def validate_video_id(video_id: str) -> bool:
    """
    Validate YouTube video ID format.
    
    Args:
        video_id: The video ID to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    if not video_id or not isinstance(video_id, str):
        return False
    
    # YouTube video IDs are 11 characters long
    if len(video_id) != 11:
        return False
    
    # Should contain only alphanumeric characters, hyphens, and underscores
    return bool(re.match(r'^[a-zA-Z0-9_-]{11}$', video_id))


def validate_channel_id(channel_id: str) -> bool:
    """
    Validate YouTube channel ID format.
    
    Args:
        channel_id: The channel ID to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    if not channel_id or not isinstance(channel_id, str):
        return False
    
    # Channel IDs start with 'UC' and are 24 characters long
    if len(channel_id) != 24 or not channel_id.startswith('UC'):
        return False
    
    # Should contain only alphanumeric characters, hyphens, and underscores
    return bool(re.match(r'^UC[a-zA-Z0-9_-]{22}$', channel_id))


def validate_output_format(format_type: str) -> bool:
    """
    Validate output format type.
    
    Args:
        format_type: The output format to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    valid_formats = ['json', 'csv', 'txt', 'xml']
    return format_type.lower() in valid_formats 