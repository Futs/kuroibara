#!/usr/bin/env python3
"""
Provider Configuration Generator

Generates provider configuration from parsed GitHub issue data.
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, Any, Optional


def clean_provider_id(provider_id: str) -> str:
    """Clean and validate provider ID."""
    # Remove spaces, convert to lowercase, keep only alphanumeric and hyphens
    cleaned = re.sub(r'[^a-zA-Z0-9\-]', '', provider_id.lower())
    return cleaned


def parse_selectors(selectors_text: str) -> Dict[str, Any]:
    """Parse and validate CSS selectors from text."""
    try:
        # Try to parse as JSON
        selectors = json.loads(selectors_text)
        
        # Validate required selector fields
        required_selectors = ['search_items', 'title', 'cover', 'link']
        for required in required_selectors:
            if required not in selectors:
                print(f"Warning: Missing required selector '{required}'")
                
        return selectors
    except json.JSONDecodeError as e:
        print(f"Error parsing selectors JSON: {e}")
        # Try to extract selectors from text format
        return extract_selectors_from_text(selectors_text)


def extract_selectors_from_text(text: str) -> Dict[str, Any]:
    """Extract selectors from plain text format."""
    selectors = {}
    
    # Common patterns for different selector types
    patterns = {
        'search_items': r'search[_\s]*items?[:\s]*([^\n]+)',
        'title': r'title[:\s]*([^\n]+)',
        'cover': r'cover[:\s]*([^\n]+)',
        'link': r'link[:\s]*([^\n]+)',
        'description': r'description[:\s]*([^\n]+)',
        'chapters': r'chapters?[:\s]*([^\n]+)',
        'pages': r'pages?[:\s]*([^\n]+)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Split by comma and clean up
            values = [v.strip().strip('"\'') for v in match.group(1).split(',')]
            selectors[key] = values
    
    return selectors


def determine_priority(priority_text: str) -> int:
    """Determine numeric priority from text."""
    priority_map = {
        'high': 10,
        'medium': 50,
        'low': 100
    }
    
    for key, value in priority_map.items():
        if key in priority_text.lower():
            return value
    
    return 100  # Default to low priority


def generate_provider_config() -> Dict[str, Any]:
    """Generate provider configuration from parsed issue data."""
    
    # Load parsed issue data
    try:
        with open('provider_config.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: provider_config.json not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing provider_config.json: {e}")
        sys.exit(1)
    
    # Validate required fields
    required_fields = ['name', 'id', 'base_url', 'search_url', 'type']
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        print(f"Error: Missing required fields: {missing_fields}")
        sys.exit(1)
    
    # Clean provider ID
    provider_id = clean_provider_id(data['id'])
    if not provider_id:
        print("Error: Invalid provider ID")
        sys.exit(1)
    
    # Determine provider class based on type
    class_mapping = {
        'generic (standard html scraping)': 'GenericProvider',
        'enhanced generic (cloudflare bypass needed)': 'EnhancedGenericProvider',
        'api-based (custom implementation needed)': 'CustomProvider'
    }
    
    provider_type = data['type'].lower()
    provider_class = class_mapping.get(provider_type, 'GenericProvider')
    
    # Parse selectors
    selectors = {}
    if data.get('selectors'):
        selectors = parse_selectors(data['selectors'])
    
    # Determine priority
    priority = determine_priority(data.get('priority', 'low'))
    
    # Check for NSFW support
    supports_nsfw = 'nsfw' in data.get('features', [])
    
    # Check for Cloudflare requirement
    requires_flaresolverr = data.get('requires_flaresolverr', False) or 'enhanced generic' in provider_type
    
    # Generate base configuration
    config = {
        "id": provider_id,
        "name": data['name'],
        "class_name": provider_class,
        "url": data['base_url'],
        "supports_nsfw": supports_nsfw,
        "priority": priority,
        "params": {
            "base_url": data['base_url'],
            "search_url": data['search_url'],
            "manga_url_pattern": f"{data['base_url'].rstrip('/')}/manga/{{manga_id}}",
            "chapter_url_pattern": f"{data['base_url'].rstrip('/')}/manga/{{manga_id}}/{{chapter_id}}",
            "name": data['name']
        }
    }
    
    # Add selectors if provided
    if selectors:
        config['params']['selectors'] = selectors
    
    # Add Cloudflare support if needed
    if requires_flaresolverr:
        config['requires_flaresolverr'] = True
        config['params']['use_flaresolverr'] = True
        config['params']['flaresolverr_url'] = "http://flaresolverr:8191"
    
    # Add additional metadata
    if data.get('additional_info'):
        config['notes'] = data['additional_info']
    
    # Add test information
    if data.get('test_manga'):
        config['test_info'] = data['test_manga']
    
    # Save generated config
    config_list = [config]
    with open('generated_provider.json', 'w') as f:
        json.dump(config_list, f, indent=2)
    
    print(f"✅ Generated provider config for {data['name']}")
    print(f"   - ID: {provider_id}")
    print(f"   - Class: {provider_class}")
    print(f"   - Priority: {priority}")
    print(f"   - NSFW: {supports_nsfw}")
    print(f"   - FlareSolverr: {requires_flaresolverr}")
    print(f"   - Selectors: {len(selectors)} defined")
    
    return config


if __name__ == '__main__':
    try:
        generate_provider_config()
        print("🎉 Provider configuration generated successfully!")
    except Exception as e:
        print(f"❌ Error generating provider config: {e}")
        sys.exit(1)
