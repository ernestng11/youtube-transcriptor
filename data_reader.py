#!/usr/bin/env python3
"""
Simple utility to read and traverse JSON files in data directories.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Generator, Optional


def traverse_json_files(limit: int = 10, data_path: str = "data/EthCC[8]RedfordStage") -> Generator[Dict[str, Any], None, None]:
    """
    Traverse JSON files in a directory and yield their contents.
    
    Args:
        limit: Maximum number of JSON files to read (default: 10)
        data_path: Path to directory containing JSON files (default: "data")
        
    Yields:
        Dict containing JSON data from each file, with added metadata:
        - '_file_path': Path to the JSON file
        - '_file_name': Name of the JSON file
        - '_directory': Directory containing the file
    """
    data_dir = Path(data_path)
    
    if not data_dir.exists():
        print(f"❌ Directory '{data_path}' does not exist")
        return
    
    if not data_dir.is_dir():
        print(f"❌ '{data_path}' is not a directory")
        return
    
    files_processed = 0
    
    # Recursively find all JSON files
    json_files = list(data_dir.rglob("*.json"))
    
    print(f"📁 Found {len(json_files)} JSON files in '{data_path}'")
    print(f"🔢 Processing up to {limit} files...")
    print("-" * 50)
    
    for json_file in json_files:
        if files_processed >= limit:
            print(f"✅ Reached limit of {limit} files")
            break
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Add metadata about the file
            data['_file_path'] = str(json_file)
            data['_file_name'] = json_file.name
            data['_directory'] = json_file.parent.name
            
            print(f"📄 {files_processed + 1}. {json_file.name}")
            
            yield data
            files_processed += 1
            
        except json.JSONDecodeError as e:
            print(f"❌ Error reading {json_file}: Invalid JSON - {e}")
            continue
        except Exception as e:
            print(f"❌ Error reading {json_file}: {e}")
            continue
    
    print(f"\n✅ Processed {files_processed} JSON files")


def read_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Read a single JSON file and return its contents.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary containing JSON data or None if error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        print(f"❌ Error reading {file_path}: Invalid JSON - {e}")
        return None
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return None
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return None


def list_json_files(data_path: str = "data") -> list:
    """
    List all JSON files in a directory.
    
    Args:
        data_path: Path to directory containing JSON files
        
    Returns:
        List of Path objects for JSON files
    """
    data_dir = Path(data_path)
    
    if not data_dir.exists():
        print(f"❌ Directory '{data_path}' does not exist")
        return []
    
    json_files = list(data_dir.rglob("*.json"))
    
    print(f"📁 Found {len(json_files)} JSON files in '{data_path}':")
    for i, file_path in enumerate(json_files, 1):
        relative_path = file_path.relative_to(data_dir)
        print(f"  {i}. {relative_path}")
    
    return json_files


# Example usage functions
def example_usage():
    """Example of how to use the traverse_json_files function."""
    
    print("🎬 YouTube Transcriptor - Data Reader")
    print("=" * 50)
    
    # Example 1: Read first 5 JSON files
    print("\n📖 Reading first 5 JSON files:")
    for data in traverse_json_files(limit=5, data_path="data"):
        print(f"  📄 File: {data['_file_name']}")
        print(f"  📁 Directory: {data['_directory']}")
        
        # Check if it's a video transcript
        if 'video_title' in data:
            print(f"  🎥 Video: {data['video_title']}")
            if 'transcript' in data:
                word_count = data['transcript'].get('word_count', 0)
                print(f"  📝 Words: {word_count:,}")
        
        # Check if it's a playlist summary
        elif 'playlist_info' in data:
            print(f"  📋 Playlist: {data['playlist_info']['title']}")
            print(f"  📊 Videos: {len(data.get('videos', []))}")
        
        print()


if __name__ == "__main__":
    example_usage() 