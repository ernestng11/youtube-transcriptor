#!/usr/bin/env python3
"""
Simple utility to parse LLM processing results.
"""

from typing import List
import re


def split_llm_result(result: str, delimiter: str = "\n<|>\n") -> List[str]:
    """
    Split LLM processing result by delimiter and clean up items.
    
    Args:
        result: The result string from LLM processing
        delimiter: The delimiter to split by (default: "\n<|>\n")
        
    Returns:
        List of split and cleaned items
    """
    if not result or not isinstance(result, str):
        return []
    
    # Split by delimiter
    items = result.split(delimiter)
    
    # Clean up items - remove empty strings and strip whitespace
    cleaned_items = []
    for item in items:
        cleaned_item = item.strip()
        if cleaned_item:  # Only keep non-empty items
            cleaned_items.append(cleaned_item)
    
    return cleaned_items


def split_llm_result_robust(result: str) -> List[str]:
    """
    Robustly split LLM result that may have entities and relationships concatenated.
    This handles cases where the result isn't properly separated by delimiters.
    
    Args:
        result: The result string from LLM processing
        
    Returns:
        List of split items (entities and relationships)
    """
    if not result or not isinstance(result, str):
        return []
    
    # Clean up the result string
    result = result.replace('\\"', '"').replace("\\'", "'")
    
    # Find all entities and relationships using regex
    # Pattern for entities: ("entity"<|>NAME<|>TYPE<|>DESCRIPTION)
    entity_pattern = r'\("entity"[^)]+\)'
    
    # Pattern for relationships: ("relationship"<|>FROM<|>TO<|>DESCRIPTION<|>SCORE)
    relationship_pattern = r'\("relationship"[^)]+\)'
    
    entities = re.findall(entity_pattern, result)
    relationships = re.findall(relationship_pattern, result)
    
    # Combine and return all items
    all_items = entities + relationships
    
    return all_items


def parse_entities_and_relationships(result: str) -> dict:
    """
    Parse LLM result specifically for entities and relationships.
    
    Args:
        result: The result string from LLM processing
        
    Returns:
        Dictionary with 'entities' and 'relationships' lists
    """
    # Try robust parsing first
    items = split_llm_result_robust(result)
    
    # If robust parsing didn't work, fall back to simple splitting
    if not items:
        items = split_llm_result(result)
    
    entities = []
    relationships = []
    
    for item in items:
        if item.startswith('("entity"'):
            entities.append(item)
        elif item.startswith('("relationship"'):
            relationships.append(item)
    
    return {
        'entities': entities,
        'relationships': relationships,
        'total_items': len(items),
        'entity_count': len(entities),
        'relationship_count': len(relationships)
    }


def extract_entity_info(entity_str: str) -> dict:
    """
    Extract information from an entity string.
    
    Args:
        entity_str: Entity string like ('entity'<|>NAME<|>TYPE<|>DESCRIPTION)
        
    Returns:
        Dictionary with extracted information
    """
    try:
        # Remove outer parentheses and quotes
        cleaned = entity_str.strip('()').strip('"')
        
        # Split by <|>
        parts = cleaned.split('<|>')
        
        if len(parts) >= 4:
            return {
                'type': 'entity',
                'name': parts[1].strip(),
                'category': parts[2].strip(),
                'description': parts[3].strip()
            }
    except:
        pass
    
    return {
        'type': 'entity',
        'name': 'Unknown',
        'category': 'Unknown',
        'description': entity_str
    }


def extract_relationship_info(relationship_str: str) -> dict:
    """
    Extract information from a relationship string.
    
    Args:
        relationship_str: Relationship string like ('relationship'<|>FROM<|>TO<|>DESCRIPTION<|>SCORE)
        
    Returns:
        Dictionary with extracted information
    """
    try:
        # Remove outer parentheses and quotes
        cleaned = relationship_str.strip('()').strip('"')
        
        # Split by <|>
        parts = cleaned.split('<|>')
        
        if len(parts) >= 5:
            return {
                'type': 'relationship',
                'from': parts[1].strip(),
                'to': parts[2].strip(),
                'description': parts[3].strip(),
                'score': parts[4].strip()
            }
    except:
        pass
    
    return {
        'type': 'relationship',
        'from': 'Unknown',
        'to': 'Unknown',
        'description': relationship_str,
        'score': '0'
    }


def save_parsed_result(result: str, filename: str, output_dir: str = "results/parsed") -> str:
    """
    Save parsed result to a text file with better formatting.
    
    Args:
        result: The result string from LLM processing
        filename: Base filename for output
        output_dir: Directory to save parsed results
        
    Returns:
        Path to saved file
    """
    from pathlib import Path
    from datetime import datetime
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Parse the result
    parsed = parse_entities_and_relationships(result)
    
    # Create formatted output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
    output_file = output_path / f"parsed_{safe_filename}_{timestamp}.txt"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Parsed LLM Result: {filename}\n")
            f.write(f"# Generated at: {datetime.now().isoformat()}\n")
            f.write(f"# Total Items: {parsed['total_items']}\n")
            f.write(f"# Entities: {parsed['entity_count']}\n")
            f.write(f"# Relationships: {parsed['relationship_count']}\n")
            f.write("=" * 60 + "\n\n")
            
            # Write entities with extracted info
            f.write("ENTITIES:\n")
            f.write("-" * 30 + "\n")
            for i, entity in enumerate(parsed['entities'], 1):
                info = extract_entity_info(entity)
                f.write(f"{i}. {info['name']} ({info['category']})\n")
                f.write(f"   Description: {info['description']}\n\n")
            
            # Write relationships with extracted info
            f.write("\nRELATIONSHIPS:\n")
            f.write("-" * 30 + "\n")
            for i, relationship in enumerate(parsed['relationships'], 1):
                info = extract_relationship_info(relationship)
                f.write(f"{i}. {info['from']} → {info['to']} (Score: {info['score']})\n")
                f.write(f"   Description: {info['description']}\n\n")
        
        print(f"💾 Parsed result saved to: {output_file}")
        return str(output_file)
        
    except Exception as e:
        print(f"❌ Error saving parsed result: {e}")
        return ""


# Example usage
def example_usage():
    """Example of how to use the parsing functions."""
    
    # Sample LLM result (truncated for example)
    sample_result = '''("entity"<|>FASTCON<|>COMPANY, ORGANIZATION<|>FastCon is a company that manufactures hardware...)
<|>
("entity"<|>AI<|>TECHNOLOGY, CONCEPT<|>AI refers to artificial intelligence...)
<|>
("relationship"<|>FASTCON<|>AI<|>FastCon integrates AI into its operations...)'''
    
    print("🔍 Parsing LLM Result")
    print("=" * 40)
    
    # Split the result (both methods)
    items_simple = split_llm_result(sample_result)
    items_robust = split_llm_result_robust(sample_result)
    
    print(f"📊 Simple split: {len(items_simple)} items")
    print(f"📊 Robust split: {len(items_robust)} items")
    
    # Parse entities and relationships
    parsed = parse_entities_and_relationships(sample_result)
    print(f"🏢 Entities: {parsed['entity_count']}")
    print(f"🔗 Relationships: {parsed['relationship_count']}")


if __name__ == "__main__":
    example_usage() 