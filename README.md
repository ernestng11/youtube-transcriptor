# YouTube Transcriptor

Extract and organize transcripts from YouTube videos and playlists with automatic file organization and comprehensive metadata.

## Installation

### Prerequisites
- Python 3.8 or higher
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management

### Setup

1. **Install dependencies with Poetry:**
   ```bash
   poetry install
   ```

2. **Activate the virtual environment:**
   ```bash
   poetry env activate
   ```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Required: YouTube Data API v3 key
YOUTUBE_API_KEY=your_youtube_api_key_here

# Optional but recommended: youtube-transcript.io API token
TRANSCRIPT_API_TOKEN=your_transcript_api_token_here
```

### Getting API Keys

1. **YouTube API Key** (Required):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the YouTube Data API v3
   - Create credentials (API Key)
   - Copy the API key to your `.env` file

2. **Transcript API Token** (Optional but recommended):
   - Visit [youtube-transcript.io](https://youtube-transcript.io/)
   - Sign up for an account
   - Get your API token from the dashboard
   - Add it to your `.env` file

## Usage

### Basic Usage

```bash
# Process a YouTube playlist
python main.py "https://www.youtube.com/playlist?list=PLExample"

# Process a single video
python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Use direct IDs
python main.py "PLExample"        # Playlist ID
python main.py "dQw4w9WgXcQ"     # Video ID
```

### Advanced Options

```bash
# Specify custom output directory
python main.py "playlist_url" --output-dir "my_transcripts"

# Enable verbose output for debugging
python main.py "playlist_url" --verbose
```

### Command Line Help

```bash
python main.py --help
```

## Output Format

The tool creates organized directories and JSON files with comprehensive data:

### Directory Structure
```
data/
├── PlaylistName/
│   ├── _playlist_summary_PlaylistName.json
│   ├── VideoTitle1_VIDEO_ID.json
│   ├── VideoTitle2_VIDEO_ID.json
│   └── ...
```

### JSON File Content

Each video transcript file contains:

```json
{
  "video_id": "dQw4w9WgXcQ",
  "video_title": "Rick Astley - Never Gonna Give You Up",
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "channel_title": "Rick Astley",
  "published_at": "2009-10-25T06:57:33Z",
  "duration_seconds": 212,
  "view_count": 1500000000,
  "description": "Video description...",
  
  "transcript": {
    "language": "en",
    "is_auto_generated": true,
    "total_segments": 45,
    "aggregated_text": "Full transcript text...",
    "text_length": 1250,
    "word_count": 200
  },
  
  "segments": [
    {
      "start": 0.0,
      "duration": 3.5,
      "text": "We're no strangers to love",
      "timestamp": "00:00"
    }
  ],
  
  "extraction_timestamp": "2024-01-15T10:30:00",
  "processing_type": "playlist"
}
```

## Examples

### Process a Conference Playlist
```bash
python main.py "https://www.youtube.com/playlist?list=PLConferenceExample" --output-dir "conference_2024"
```

### Process Educational Content
```bash
python main.py "https://www.youtube.com/watch?v=educational_video_id" --verbose
```

## Success Rate & Statistics

The tool provides detailed statistics after processing:

```
✅ SUCCESS!
📋 Playlist: AI Conference 2024
🎭 Channel: TechConf
📊 Videos: 25
✅ Transcripts: 23
❌ Failed: 2
📈 Success Rate: 92.0%
⏱️  Processing Time: 45.2s
📁 Output Directory: data/AIConference2024
```

## Troubleshooting

### Common Issues

1. **API Key Error**: Make sure your `YOUTUBE_API_KEY` is set correctly in `.env`
2. **No Transcripts Found**: Some videos don't have transcripts available
3. **Rate Limiting**: The tool includes automatic retry logic for rate limits
4. **Quota Exceeded**: YouTube API has daily quotas - check your usage

### Tips for Better Results

- Use the `TRANSCRIPT_API_TOKEN` for higher success rates
- Process smaller playlists if you encounter quota issues
- Check the verbose output (`--verbose`) for detailed error information

## API Limits

- **YouTube Data API**: 10,000 quota units per day (free tier)
- **youtube-transcript.io**: Varies by plan (check their pricing)

## Contributing

Feel free to submit issues and pull requests to improve the tool!

## License

This project is open source. Please check the license file for details.
