"""Command line interface for YouTube Transcriptor."""

import json
import csv
import sys
import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint

from ..core.playlist_extractor import PlaylistExtractor
from ..core.transcript_extractor import TranscriptExtractor
from ..core.pipeline import TranscriptionPipeline
from ..core.models import PlaylistSearchResults
from ..config.settings import settings
from ..utils.helpers import format_duration, format_number, truncate_text
from ..utils.validators import validate_playlist_url, validate_api_key


console = Console()
logger = logging.getLogger(__name__)


@click.group()
@click.option('--api-key', envvar='YOUTUBE_API_KEY', help='YouTube Data API key')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, api_key: Optional[str], verbose: bool):
    """YouTube Transcriptor - Extract videos from YouTube playlists."""
    
    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Store context
    ctx.ensure_object(dict)
    ctx.obj['api_key'] = api_key
    ctx.obj['verbose'] = verbose
    
    # Validate API key if provided
    if api_key and not validate_api_key(api_key):
        rprint("[bold red]Warning:[/bold red] API key format looks invalid")


@cli.command()
@click.argument('playlist_url')
@click.option('--output', '-o', type=click.Choice(['json', 'csv', 'table']), 
              default='table', help='Output format')
@click.option('--file', '-f', type=click.Path(), help='Output file path')
@click.option('--auto-name', is_flag=True, 
              help='Auto-name file using playlist title and save to data/ directory')
@click.option('--include-description', is_flag=True, 
              help='Include video descriptions in output')
@click.pass_context
def extract(ctx, playlist_url: str, output: str, file: Optional[str], 
           auto_name: bool, include_description: bool):
    """Extract videos from a YouTube playlist."""
    
    api_key = ctx.obj.get('api_key')
    
    # Validate inputs
    if not validate_playlist_url(playlist_url):
        rprint("[bold red]Error:[/bold red] Invalid playlist URL or ID")
        sys.exit(1)
    
    if not api_key:
        rprint("[bold red]Error:[/bold red] YouTube API key is required")
        rprint("Set it via --api-key option or YOUTUBE_API_KEY environment variable")
        sys.exit(1)
    
    # Extract playlist data
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Extracting playlist data...", total=None)
            
            extractor = PlaylistExtractor(api_key)
            result = extractor.extract_playlist(playlist_url)
            
            progress.update(task, description="Extraction complete!")
        
        if not result.success:
            rprint(f"[bold red]Error:[/bold red] {result.error_message}")
            sys.exit(1)
        
        # Handle auto-naming
        output_file = file
        if auto_name and output in ['json', 'csv'] and result.playlist_data:
            from ..utils.helpers import sanitize_filename
            playlist_title = result.playlist_data.playlist_info.title
            safe_title = sanitize_filename(playlist_title)
            extension = 'json' if output == 'json' else 'csv'
            output_file = f"data/{safe_title}.{extension}"
        
        # Display results
        _display_results(result, output, output_file, include_description)
        
    except KeyboardInterrupt:
        rprint("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        rprint(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Choice(['json', 'csv']), 
              default='json', help='Output format')
@click.option('--output-dir', '-d', type=click.Path(), default='./results',
              help='Output directory for results')
@click.pass_context
def batch_extract(ctx, file_path: str, output: str, output_dir: str):
    """Extract multiple playlists from a file containing URLs."""
    
    api_key = ctx.obj.get('api_key')
    
    if not api_key:
        rprint("[bold red]Error:[/bold red] YouTube API key is required")
        sys.exit(1)
    
    # Read URLs from file
    try:
        with open(file_path, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except Exception as e:
        rprint(f"[bold red]Error reading file:[/bold red] {e}")
        sys.exit(1)
    
    if not urls:
        rprint("[bold red]Error:[/bold red] No URLs found in file")
        sys.exit(1)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Process each URL
    extractor = PlaylistExtractor(api_key)
    
    with Progress(console=console) as progress:
        task = progress.add_task("Processing playlists...", total=len(urls))
        
        for i, url in enumerate(urls):
            progress.update(task, description=f"Processing playlist {i+1}/{len(urls)}")
            
            if not validate_playlist_url(url):
                rprint(f"[yellow]Skipping invalid URL:[/yellow] {url}")
                continue
            
            try:
                result = extractor.extract_playlist(url)
                
                if result.success:
                    # Save to file
                    filename = f"playlist_{i+1}.{output}"
                    filepath = output_path / filename
                    
                    if output == 'json':
                        _save_json(result.playlist_data, str(filepath))
                    else:
                        _save_csv(result.playlist_data, str(filepath))
                    
                    rprint(f"[green]✓[/green] Saved: {filepath}")
                else:
                    rprint(f"[red]✗[/red] Failed: {url} - {result.error_message}")
                    
            except Exception as e:
                rprint(f"[red]✗[/red] Error processing {url}: {e}")
                continue
            
            progress.advance(task)
    
    rprint(f"\n[bold green]Batch extraction complete![/bold green]")
    rprint(f"Results saved to: {output_path}")


@cli.command()
@click.argument('search_query')
@click.option('--playlist', '-p', help='Playlist URL to search in')
@click.option('--json-file', '-j', type=click.Path(exists=True), 
              help='Search in existing JSON file')
@click.option('--case-sensitive', is_flag=True, 
              help='Make search case sensitive')
@click.option('--max-results', type=int, default=20, 
              help='Maximum number of results to show')
@click.option('--web-api', is_flag=True, default=True,
              help='Use youtube-transcript.io web API (default: enabled)')
@click.option('--youtube-api-only', is_flag=True,
              help='Use only YouTube transcript API (disables web API)')
@click.pass_context
def search(ctx, search_query: str, playlist: Optional[str], json_file: Optional[str], 
          case_sensitive: bool, max_results: int, web_api: bool, youtube_api_only: bool):
    """Search for text across video transcripts."""
    
    api_key = ctx.obj.get('api_key')
    
    if not playlist and not json_file:
        rprint("[bold red]Error:[/bold red] Must specify either --playlist or --json-file")
        sys.exit(1)
    
    if playlist and json_file:
        rprint("[bold red]Error:[/bold red] Cannot specify both --playlist and --json-file")
        sys.exit(1)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Get playlist data
            if playlist:
                if not api_key:
                    rprint("[bold red]Error:[/bold red] YouTube API key is required for playlist extraction")
                    sys.exit(1)
                
                if not validate_playlist_url(playlist):
                    rprint("[bold red]Error:[/bold red] Invalid playlist URL or ID")
                    sys.exit(1)
                
                task = progress.add_task("Extracting playlist data...", total=None)
                extractor = PlaylistExtractor(api_key)
                result = extractor.extract_playlist(playlist)
                
                if not result.success or not result.playlist_data:
                    rprint(f"[bold red]Error:[/bold red] {result.error_message}")
                    sys.exit(1)
                
                playlist_data = result.playlist_data
            else:
                # Load from JSON file
                task = progress.add_task("Loading playlist data...", total=None)
                import json
                from ..core.models import PlaylistData
                
                if not json_file:
                    rprint("[bold red]Error:[/bold red] JSON file path is required")
                    sys.exit(1)
                
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                playlist_data = PlaylistData(**data)
            
            progress.update(task, description="Extracting transcripts...")
            
            # Determine API usage
            use_web_api = web_api and not youtube_api_only
            
            # Extract transcripts
            transcript_extractor = TranscriptExtractor(use_web_api=use_web_api)
            transcripts = transcript_extractor.extract_playlist_transcripts(playlist_data)
            
            if not transcripts:
                rprint("[yellow]Warning:[/yellow] No transcripts found in any videos")
                sys.exit(1)
            
            progress.update(task, description=f"Searching for '{search_query}'...")
            
            # Search transcripts
            search_results = transcript_extractor.search_transcripts(
                transcripts, search_query, case_sensitive
            )
            search_results.playlist_title = playlist_data.playlist_info.title
            
            progress.update(task, description="Search complete!")
        
        # Display results
        _display_search_results(search_results, max_results)
        
    except KeyboardInterrupt:
        rprint("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        rprint(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


def _display_search_results(results: 'PlaylistSearchResults', max_results: int):
    """Display search results in a formatted table."""
    
    # Search summary panel
    summary_text = f"""[bold]Query:[/bold] "{results.query}"
[bold]Playlist:[/bold] {results.playlist_title}
[bold]Total Results:[/bold] {results.total_results}
[bold]Videos Searched:[/bold] {results.searched_videos}
[bold]Search Time:[/bold] {results.search_time_seconds:.2f}s"""
    
    console.print(Panel(summary_text, title="🔍 Search Results", expand=False))
    console.print()
    
    if results.total_results == 0:
        rprint("[yellow]No results found.[/yellow]")
        return
    
    # Results table
    table = Table(title=f"📝 Matches (showing first {min(max_results, results.total_results)})")
    table.add_column("Video", style="cyan", max_width=30)
    table.add_column("Time", justify="center", style="green")
    table.add_column("Context", max_width=60)
    
    displayed = 0
    for result in results.results[:max_results]:
        # Format timestamp
        timestamp = f"{int(result.segment.start // 60):02d}:{int(result.segment.start % 60):02d}"
        
        # Build context
        context_parts = []
        if result.context_before:
            context_parts.append(f"[dim]{result.context_before}[/dim]")
        
        # Highlight the matching segment
        segment_text = result.segment.text
        context_parts.append(f"[bold yellow]{segment_text}[/bold yellow]")
        
        if result.context_after:
            context_parts.append(f"[dim]{result.context_after}[/dim]")
        
        context = " ".join(context_parts)
        
        table.add_row(
            result.video_title,
            timestamp,
            context
        )
        
        displayed += 1
    
    console.print(table)
    
    if results.total_results > max_results:
        rprint(f"\n[dim]Showing {displayed} of {results.total_results} results. Use --max-results to see more.[/dim]")


def _display_results(result, output_format: str, output_file: Optional[str], 
                    include_description: bool):
    """Display extraction results in the specified format."""
    
    playlist_data = result.playlist_data
    
    if output_format == 'table':
        _display_table(playlist_data, include_description)
    elif output_format == 'json':
        if output_file:
            _save_json(playlist_data, output_file)
            rprint(f"[green]Results saved to:[/green] {output_file}")
        else:
            print(json.dumps(playlist_data.dict(), indent=2, default=str))
    elif output_format == 'csv':
        if output_file:
            _save_csv(playlist_data, output_file)
            rprint(f"[green]Results saved to:[/green] {output_file}")
        else:
            rprint("[yellow]CSV output requires --file option[/yellow]")


def _display_table(playlist_data, include_description: bool):
    """Display results in a formatted table."""
    
    # Playlist info panel
    info_text = f"""[bold]Title:[/bold] {playlist_data.playlist_info.title}
[bold]Channel:[/bold] {playlist_data.playlist_info.channel_title}
[bold]Videos:[/bold] {len(playlist_data.videos)}
[bold]Total Duration:[/bold] {format_duration(playlist_data.total_duration_seconds)}"""
    
    console.print(Panel(info_text, title="📋 Playlist Information", expand=False))
    console.print()
    
    # Videos table
    table = Table(title="🎥 Videos")
    table.add_column("Title", style="cyan", no_wrap=False, max_width=40)
    table.add_column("Channel", style="green", max_width=20)
    table.add_column("Duration", justify="center")
    table.add_column("Views", justify="right")
    table.add_column("Published", justify="center")
    
    if include_description:
        table.add_column("Description", max_width=30)
    
    for video in playlist_data.videos:
        row = [
            video.title,
            video.channel_title,
            format_duration(video.duration_seconds),
            format_number(video.view_count),
            video.published_at.strftime("%Y-%m-%d") if video.published_at else "N/A"
        ]
        
        if include_description:
            row.append(truncate_text(video.description, 50))
        
        table.add_row(*row)
    
    console.print(table)


def _save_json(playlist_data, filepath: str):
    """Save playlist data as JSON."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(playlist_data.dict(), f, indent=2, default=str, ensure_ascii=False)


def _save_csv(playlist_data, filepath: str):
    """Save playlist data as CSV."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'Video ID', 'Title', 'Channel', 'Duration (seconds)', 
            'Views', 'Likes', 'Comments', 'Published', 'Description'
        ])
        
        # Data
        for video in playlist_data.videos:
            writer.writerow([
                video.id,
                video.title,
                video.channel_title,
                video.duration_seconds or 0,
                video.view_count or 0,
                video.like_count or 0,
                video.comment_count or 0,
                video.published_at.isoformat() if video.published_at else '',
                video.description or ''
            ])


@cli.command()
@click.argument('playlist_url')
@click.option('--output-dir', '-d', default='data', 
              help='Base output directory for organized transcripts')
@click.option('--web-api/--no-web-api', default=True,
              help='Use youtube-transcript.io web API (recommended)')
@click.pass_context
def transcribe(ctx, playlist_url: str, output_dir: str, web_api: bool):
    """Complete pipeline: extract playlist and save organized transcript files."""
    
    api_key = ctx.obj.get('api_key')
    
    if not validate_playlist_url(playlist_url):
        rprint("[bold red]Error:[/bold red] Invalid playlist URL or ID")
        sys.exit(1)
    
    if not api_key:
        rprint("[bold red]Error:[/bold red] YouTube API key is required")
        rprint("Set it via --api-key option or YOUTUBE_API_KEY environment variable")
        sys.exit(1)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Initialize pipeline
            task = progress.add_task("Initializing pipeline...", total=None)
            pipeline = TranscriptionPipeline(api_key, use_web_api=web_api)
            
            # Process playlist
            progress.update(task, description="Processing playlist...")
            results = pipeline.process_playlist(playlist_url, output_dir)
            
            progress.update(task, description="Pipeline complete!")
        
        # Display results
        if results["success"]:
            _display_pipeline_results(results)
        else:
            rprint(f"[bold red]Pipeline failed:[/bold red]")
            for error in results["errors"]:
                rprint(f"  • {error}")
            sys.exit(1)
        
    except KeyboardInterrupt:
        rprint("\n[yellow]Pipeline cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        rprint(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


def _display_pipeline_results(results):
    """Display pipeline processing results."""
    
    # Pipeline summary panel
    playlist_data = results["playlist_data"]
    summary_text = f"""[bold]Playlist:[/bold] {playlist_data["title"]}
[bold]Channel:[/bold] {playlist_data["channel"]}
[bold]Videos Found:[/bold] {playlist_data["video_count"]}
[bold]Transcripts Processed:[/bold] {results["transcripts_processed"]}
[bold]Failed:[/bold] {results["transcripts_failed"]}
[bold]Success Rate:[/bold] {(results["transcripts_processed"]/playlist_data["video_count"]*100):.1f}%
[bold]Output Directory:[/bold] {results["output_directory"]}"""
    
    console.print(Panel(summary_text, title="🎬 Pipeline Results", expand=False))
    console.print()
    
    # Files saved
    rprint(f"[green]📁 Files created:[/green]")
    for file_path in results["saved_files"]:
        filename = file_path.split('/')[-1]  # Get just the filename
        rprint(f"  • {filename}")
    
    rprint(f"\n[green]✅ Pipeline completed successfully![/green]")
    rprint(f"[dim]Check the output directory for individual video transcript files[/dim]")


if __name__ == '__main__':
    cli(obj={}) 