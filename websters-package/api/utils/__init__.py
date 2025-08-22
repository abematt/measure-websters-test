import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from llama_index.core.vector_stores.types import MetadataFilters, MetadataFilter

def clean_response_text(response_text):
    """Remove inline citations and markdown links from response"""
    if not isinstance(response_text, str):
        return str(response_text)
    
    # Remove markdown links [text](url) 
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', response_text)
    
    # Remove any remaining parenthetical content with URLs (most aggressive)
    cleaned = re.sub(r'\([^)]*https?://[^)]*\)', '', cleaned)
    
    # Remove bare URLs anywhere in text
    cleaned = re.sub(r'https?://[^\s\)\]\.\\,]+[^\s\)\]\.\\,]*', '', cleaned)
    
    # Remove any remaining parentheses that might have URLs
    cleaned = re.sub(r'\([^)]*\.com[^)]*\)', '', cleaned)
    cleaned = re.sub(r'\([^)]*\.org[^)]*\)', '', cleaned)
    cleaned = re.sub(r'\([^)]*\.net[^)]*\)', '', cleaned)
    
    # Clean up citation patterns like ". (source.com)" or ". [source.com]"
    cleaned = re.sub(r'\.\s*\([^)]*\)', '.', cleaned)
    cleaned = re.sub(r'\.\s*\[[^\]]*\]', '.', cleaned)
    
    # Remove any hanging punctuation from URL removal
    cleaned = re.sub(r'\s*\)\)', ')', cleaned)
    cleaned = re.sub(r'\s*\]\]', ']', cleaned)
    
    # Clean up extra whitespace and punctuation
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\s+\.', '.', cleaned)
    cleaned = re.sub(r'\.+', '.', cleaned)
    cleaned = re.sub(r'\s+\)', ')', cleaned)
    cleaned = re.sub(r'\(\s+', '(', cleaned)
    
    return cleaned.strip()

def load_source_preferences():
    """Load source preferences from configuration file"""
    config_path = Path(__file__).parent.parent.parent / "config" / "source_preferences.yaml"
    if config_path.exists():
        print("Loading Source Preferences")
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return None

def build_metadata_filters(filters: Dict[str, Any]) -> Optional[MetadataFilters]:
    """Build metadata filters from request filters"""
    if not filters:
        return None
        
    metadata_filters = []
    
    if 'category' in filters:
        metadata_filters.append(
            MetadataFilter(key="category", value=filters['category'])
        )
    
    if 'platform' in filters:
        metadata_filters.append(
            MetadataFilter(key="platform", value=filters['platform'])
        )
    
    if 'tags' in filters:
        for tag in filters['tags']:
            metadata_filters.append(
                MetadataFilter(key="tags", value=tag)
            )
    
    if 'source_type' in filters:
        metadata_filters.append(
            MetadataFilter(key="source_type", value=filters['source_type'])
        )
    
    return MetadataFilters(filters=metadata_filters) if metadata_filters else None

def get_source_instruction_and_format(nodes, preferences) -> Tuple[str, Dict]:
    """Get source instruction and response format based on detected categories and platforms"""
    if not preferences:
        return "", {}
    
    categories = set()
    platforms = set()
    datatypes = set()
    
    for node in nodes:
        metadata = node.node.metadata if hasattr(node, 'node') else node.get('metadata', {})
        if 'category' in metadata:
            categories.add(metadata['category'])
        if 'platform' in metadata:
            platforms.add(metadata['platform'])
        if 'datatype' in metadata:
            # Extract the main type (e.g., 'tiktok' from 'social.tiktok')
            datatype = metadata['datatype']
            if '.' in datatype:
                parts = datatype.split('.')
                if len(parts) > 1:
                    datatypes.add(parts[1])  # Get platform from datatype
    
    instructions = []
    sources = []
    
    # Check category-specific preferences
    for category in categories:
        if category in preferences['source_preferences']['by_category']:
            cat_prefs = preferences['source_preferences']['by_category'][category]
            
            # Check for specific platforms within category
            for platform in datatypes:
                if platform in cat_prefs:
                    platform_prefs = cat_prefs[platform]
                    instructions.append(platform_prefs.get('instruction', ''))
                    sources.extend(platform_prefs.get('preferred_sources', []))
    
    # Check platform-specific preferences
    for platform in platforms:
        if platform in preferences['source_preferences']['by_platform']:
            plat_prefs = preferences['source_preferences']['by_platform'][platform]
            if plat_prefs.get('instruction') not in instructions:
                instructions.append(plat_prefs.get('instruction', ''))
            sources.extend(plat_prefs.get('preferred_sources', []))
    
    # Build final instruction
    if instructions:
        instruction = " ".join(instructions)
    else:
        instruction = preferences['source_preferences']['default']['instruction']
    
    if sources:
        # Deduplicate sources
        unique_sources = list(dict.fromkeys(sources))
        instruction += f" Preferred sources: {', '.join(unique_sources[:3])}"
    
    # Get response format preferences
    response_format = preferences.get('response_format', {
        'data_focus_ratio': 80,
        'context_ratio': 20,
        'max_context_sentences': 2
    })
    
    return instruction, response_format

def get_source_instruction(nodes, preferences) -> str:
    """Backward compatibility wrapper"""
    instruction, _ = get_source_instruction_and_format(nodes, preferences)
    return instruction

def extract_metadata_context(nodes, preferences=None) -> Dict[str, Any]:
    """Extract metadata context for potential web search"""
    categories = set()
    platforms = set()
    datatypes = set()
    tags = set()
    
    for node in nodes:
        metadata = node.node.metadata if hasattr(node, 'node') else node.get('metadata', {})
        if 'category' in metadata:
            categories.add(metadata['category'])
        if 'platform' in metadata:
            platforms.add(metadata['platform'])
        if 'datatype' in metadata:
            datatypes.add(metadata['datatype'])
        if 'tags' in metadata:
            tags.update(metadata.get('tags', []))
    
    # Determine preferred sources based on metadata
    preferred_sources = []
    search_instructions = []
    
    if preferences:
        for category in categories:
            if category in preferences['source_preferences']['by_category']:
                cat_prefs = preferences['source_preferences']['by_category'][category]
                for datatype in datatypes:
                    if '.' in datatype:
                        _, platform_type = datatype.split('.', 1)
                        if platform_type in cat_prefs:
                            platform_prefs = cat_prefs[platform_type]
                            preferred_sources.extend(platform_prefs.get('preferred_sources', []))
                            search_instructions.append(platform_prefs.get('instruction', ''))
    
    # Create concise context summary
    context_summary = []
    if categories:
        context_summary.append(f"Categories: {', '.join(categories)}")
    if platforms:
        context_summary.append(f"Platforms: {', '.join(platforms)}")
    if datatypes:
        context_summary.append(f"Data types: {', '.join(list(datatypes)[:3])}")
    
    return {
        'categories': list(categories),
        'platforms': list(platforms),
        'datatypes': list(datatypes),
        'tags': list(tags),
        'preferred_sources': list(dict.fromkeys(preferred_sources)),  # Remove duplicates
        'search_instructions': list(dict.fromkeys(search_instructions)),
        'context_summary': ' | '.join(context_summary)
    }