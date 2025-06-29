"""Configuration settings for YouTube Transcriptor."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # YouTube API Configuration
        self.youtube_api_key: Optional[str] = os.getenv("YOUTUBE_API_KEY")
        self.youtube_api_service_name: str = "youtube"
        self.youtube_api_version: str = "v3"
        self.max_results_per_request: int = 50
        self.request_timeout: int = 30
        self.max_retries: int = 3
        self.retry_delay: float = 1.0
        
        # Transcript API Configuration (youtube-transcript.io)
        self.transcript_api_token: Optional[str] = os.getenv("TRANSCRIPT_API_TOKEN")
        self.transcript_country_code: str = os.getenv("TRANSCRIPT_COUNTRY_CODE", "us")
        self.transcript_batch_size: int = int(os.getenv("TRANSCRIPT_BATCH_SIZE", "50"))
        self.transcript_rate_limit_requests: int = int(os.getenv("TRANSCRIPT_RATE_LIMIT_REQUESTS", "5"))
        self.transcript_rate_limit_window: int = int(os.getenv("TRANSCRIPT_RATE_LIMIT_WINDOW", "10"))
        
    def validate(self) -> bool:
        """Validate that required settings are present."""
        if not self.youtube_api_key:
            raise ValueError(
                "YOUTUBE_API_KEY is required. Please set it in your .env file or environment variables."
            )
        return True


# Global settings instance
settings = Settings() 