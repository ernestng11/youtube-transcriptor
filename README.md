# YouTube Transcriptor

## What It Is
A comprehensive Python tool that combines YouTube transcript extraction with AI-powered analysis using Large Language Models (LLMs). It automatically downloads transcripts from YouTube videos, processes them with configurable AI prompts, and generates structured analysis reports with comprehensive metadata.

## How It Works
The tool operates through a three-stage pipeline:

1. **Transcript Extraction**: Uses YouTube Data API v3 and optional web transcript APIs to download video transcripts, metadata, and segment information
2. **AI Analysis**: Processes the transcript text through configurable LLM providers (OpenAI GPT-4, Anthropic Claude) using custom prompts
3. **Result Generation**: Creates organized output directories containing the raw transcript data, AI analysis results, and configuration files

The workflow is driven by YAML configuration files that allow users to customize prompts, select LLM providers/models, and specify target videos or playlists. The tool handles both single video processing and playlist batch operations with automatic file organization and sanitization.

## Why It Matters
This tool solves several key challenges in content analysis and research:

- **Content Accessibility**: Transforms video content into searchable, analyzable text data
- **AI-Powered Insights**: Leverages state-of-the-art LLMs to extract key concepts, summarize discussions, and identify important themes
- **Research Efficiency**: Automates the labor-intensive process of manually transcribing and analyzing video content
- **Scalable Analysis**: Enables batch processing of multiple videos with consistent analysis frameworks
- **Structured Output**: Provides organized, metadata-rich results that can be easily integrated into research workflows, content creation, or knowledge management systems

Perfect for researchers, content creators, educators, and anyone needing to extract insights from YouTube video content at scale.

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

# Required for LLM analysis: OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Anthropic API key (alternative to OpenAI)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
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

3. **OpenAI API Key** (Required for LLM analysis):
   - Visit [OpenAI Platform](https://platform.openai.com/)
   - Create an account and get your API key
   - Add it to your `.env` file

## LLM Analysis with YAML Configuration

The tool now includes `run_llm_on_transcript.py` for automated LLM analysis of transcripts using YAML configuration.

### Setup YAML Configuration

Create a `config.yaml` file in the project root:

```yaml
prompts:
  custom: |
    You are an expert technical writer and editor specializing in artificial intelligence and emerging technologies. 
    You excel at transforming complex transcripts into clear, structured, and engaging articles for both technical and non-technical audiences. 
    Your approach is analytical and factual: you rely solely on the given transcript, avoid assumptions, and organize information in a logical, reader-friendly way. 
    Your writing is concise, professional, and geared toward conveying both the details and the significance of the topic.

    Please analyze the provided video transcript and provide:
    1. A comprehensive summary of the main topics discussed
    2. Key technical concepts and their explanations
    3. Practical applications or implications mentioned
    4. Any notable insights or conclusions

    Format your response as a structured analysis with clear sections and bullet points.

llm:
  provider: "openai"
  model: "gpt-4o-mini"

videos:
  id: "dQw4w9WgXcQ"

playlists:
  id: ""
```

### Run LLM Analysis

```bash
# Use default config.yaml
poetry run python run_llm_on_transcript.py

# Use custom config file
poetry run python run_llm_on_transcript.py --config my_config.yaml
```

### YAML Configuration Options

- **`prompts.custom`**: Your custom prompt for LLM analysis (supports multi-line)
- **`llm.provider`**: LLM provider (openai, anthropic)
- **`llm.model`**: Model name (gpt-4o-mini, claude-3-sonnet, etc.)
- **`videos.id`**: YouTube video ID to analyze (leave empty to allow any video)
- **`playlists.id`**: YouTube playlist ID to analyze (leave empty to allow any playlist)

### Example Output

```
🎬 YouTube Transcript LLM Processor
==================================================
🔧 Initialized YouTube LLM Processor
✅ YouTube API: SET
✅ Transcript API: SET
📄 Config: config.yaml

🎥 Processing Video ID: dQw4w9WgXcQ
--------------------------------------------------
✅ Transcript extracted successfully!
📹 Video: Rick Astley - Never Gonna Give You Up
🎭 Channel: Rick Astley
🌍 Language: en
📊 Segments: 45
📝 Words: 200
⏱️  Extraction Time: 0.89s

🤖 Processing with LLM (openai/gpt-4o-mini)
--------------------------------------------------
✅ LLM processing completed!
⏱️  Processing Time: 3.96s

💾 Results saved:
   📄 JSON: results/Rick_Astley_Never_Gonna_Give_You_Up/transcript.json
   📝 Text: results/Rick_Astley_Never_Gonna_Give_You_Up/analysis.txt
   ⚙️  Config: results/Rick_Astley_Never_Gonna_Give_You_Up/config.yaml

==================================================
📋 ANALYSIS RESULTS
==================================================
- **Main Theme**: The video discusses...
- **Key Points**: 
  - Point 1
  - Point 2
  - Point 3
- **Conclusion**: Summary of findings
```

## Output Format

The tool creates organized directories and files with comprehensive data:

### Directory Structure for LLM Analysis
```
results/
├── VideoTitle1/
│   ├── transcript.json      # Raw transcript data
│   ├── analysis.txt         # LLM analysis output
│   └── config.yaml          # Configuration used for analysis
├── VideoTitle2/
│   ├── transcript.json
│   ├── analysis.txt
│   └── config.yaml
└── ...
```

### LLM Analysis Output Files

#### `transcript.json`
Contains the complete transcript data extracted from the YouTube video, including metadata, segments, and processing information.

#### `analysis.txt`
Contains the LLM-generated analysis based on your custom prompt. The content varies depending on your prompt configuration.

#### `config.yaml`
A copy of the configuration file used for the analysis, including:
- Custom prompt
- LLM provider and model settings
- Video/playlist ID

### File Naming Convention

- **Directory names**: Sanitized video titles (spaces/special chars replaced with underscores)
- **JSON file**: Always named `transcript.json`
- **Text file**: Always named `analysis.txt`
- **Config file**: Always named `config.yaml`

### Example Output Flow

1. **Run Analysis**: `poetry run python run_llm_on_transcript.py`
2. **Extract Transcript**: Downloads and processes video transcript
3. **LLM Processing**: Analyzes transcript with your custom prompt
4. **Save Results**: Creates directory and saves three files:
   ```
   results/
   └── Building_a_Smarter_AI_Agent_with_Neural_RAG/
       ├── transcript.json
       ├── analysis.txt
       └── config.yaml
   ```
5. **Display Results**: Shows analysis in terminal and file paths saved
