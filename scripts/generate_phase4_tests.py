#!/usr/bin/env python3
"""
Generate individual test scripts for Phase 4 - High Volume Untested Providers
Creates test scripts for the high-priority untested providers from the analysis.
"""

import os
from pathlib import Path

# Phase 4 providers from the analysis
PHASE4_PROVIDERS = [
    {
        'name': 'MangaOnlineFun',
        'description': 'Phase 4 - High Volume Untested Provider (67,154 manga, NSFW content)',
        'url': 'https://mangaonlinefun.com'
    },
    {
        'name': 'MangaForest', 
        'description': 'Phase 4 - High Volume Untested Provider (53,153 manga, NSFW content)',
        'url': 'https://mangaforest.me'
    },
    {
        'name': 'TrueManga',
        'description': 'Phase 4 - High Volume Untested Provider (53,153 manga, NSFW content)', 
        'url': 'https://truemanga.com'
    },
    {
        'name': 'ReadComicsOnlineLi',
        'description': 'Phase 4 - High Volume Untested Provider (33,986 comics, NSFW content)',
        'url': 'https://readcomicsonline.li'
    },
    {
        'name': 'MangaFoxFun',
        'description': 'Phase 4 - High Volume Untested Provider (25,423 manga, NSFW content)',
        'url': 'https://mangafoxfun.com'
    },
    {
        'name': 'MangaHereFun',
        'description': 'Phase 4 - High Volume Untested Provider (22,228 manga)',
        'url': 'https://mangaherefun.com'
    }
]

TEST_TEMPLATE = '''#!/usr/bin/env python3
"""
Individual Provider Test: {provider_name}
Tests {provider_name} provider comprehensively with detailed debugging output and result logging.
{description}
"""

import asyncio
import logging
import sys
import traceback
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import uuid

# Add the backend directory to the path
sys.path.append('/home/futs/Apps/kuroibara')
sys.path.append('/home/futs/Apps/kuroibara/backend')

from app.core.providers.registry import provider_registry
from app.db.session import AsyncSessionLocal
from app.models.manga import Manga, Chapter
from app.models.library import MangaUserLibrary
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_QUERIES = ['naruto', 'one piece', 'attack on titan', 'demon slayer', 'dragon ball']
PROVIDER_NAME = "{provider_name}"

class ProviderTestResult:
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.search_success = False
        self.search_results_count = 0
        self.search_error = ''
        self.manga_details_success = False
        self.manga_details_error = ''
        self.chapters_success = False
        self.chapters_count = 0
        self.chapters_error = ''
        self.download_success = False
        self.download_error = ''
        self.test_manga_title = ''
        self.test_manga_id = ''
        self.pages_count = 0
        self.test_timestamp = datetime.now().isoformat()
        self.test_duration = 0.0
        self.start_time = time.time()
        
    def finish_test(self):
        """Mark test as finished and calculate duration."""
        self.test_duration = time.time() - self.start_time
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {{
            'provider_name': self.provider_name,
            'test_timestamp': self.test_timestamp,
            'test_duration': self.test_duration,
            'search': {{
                'success': self.search_success,
                'results_count': self.search_results_count,
                'error': self.search_error
            }},
            'details': {{
                'success': self.manga_details_success,
                'error': self.manga_details_error
            }},
            'chapters': {{
                'success': self.chapters_success,
                'count': self.chapters_count,
                'error': self.chapters_error
            }},
            'pages': {{
                'success': self.download_success,
                'count': self.pages_count,
                'error': self.download_error
            }},
            'test_manga': {{
                'title': self.test_manga_title,
                'id': self.test_manga_id
            }},
            'overall_status': self.get_overall_status()
        }}
        
    def get_overall_status(self) -> str:
        """Get overall provider status."""
        if self.download_success:
            return "FULLY_WORKING"
        elif self.chapters_success:
            return "PARTIALLY_WORKING_NO_PAGES"
        elif self.search_success:
            return "PARTIALLY_WORKING_SEARCH_ONLY"
        else:
            return "NOT_WORKING"

def save_test_result(result: ProviderTestResult) -> None:
    """Save test result to JSON file."""
    # Create results directory if it doesn't exist
    results_dir = Path(__file__).parent.parent / 'test_results'
    results_dir.mkdir(exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{{result.provider_name.lower()}}_{{timestamp}}.json"
    filepath = results_dir / filename
    
    # Save result
    with open(filepath, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)
    
    print(f"💾 Test result saved to: {{filepath}}")

def save_summary_result(result: ProviderTestResult) -> None:
    """Save/update summary result file."""
    # Create results directory if it doesn't exist
    results_dir = Path(__file__).parent.parent / 'test_results'
    results_dir.mkdir(exist_ok=True)
    
    summary_file = results_dir / 'provider_summary.json'
    
    # Load existing summary or create new one
    if summary_file.exists():
        with open(summary_file, 'r') as f:
            summary = json.load(f)
    else:
        summary = {{
            'last_updated': '',
            'total_providers': 0,
            'providers': {{}}
        }}
    
    # Update summary with new result
    summary['last_updated'] = datetime.now().isoformat()
    summary['providers'][result.provider_name] = {{
        'last_tested': result.test_timestamp,
        'status': result.get_overall_status(),
        'search_success': result.search_success,
        'chapters_success': result.chapters_success,
        'pages_success': result.download_success,
        'search_results': result.search_results_count,
        'chapters_count': result.chapters_count,
        'pages_count': result.pages_count,
        'test_duration': result.test_duration
    }}
    
    # Update total count
    summary['total_providers'] = len(summary['providers'])
    
    # Save updated summary
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"📊 Summary updated: {{summary_file}}")

def generate_markdown_report() -> None:
    """Generate a markdown report from test results."""
    results_dir = Path(__file__).parent.parent / 'test_results'
    summary_file = results_dir / 'provider_summary.json'
    
    if not summary_file.exists():
        print("⚠️  No summary file found, skipping markdown report")
        return
    
    with open(summary_file, 'r') as f:
        summary = json.load(f)
    
    # Generate markdown report
    report_lines = [
        "# Provider Test Results",
        "",
        f"**Last Updated:** {{summary.get('last_updated', 'Unknown')}}",
        f"**Total Providers:** {{summary.get('total_providers', 0)}}",
        "",
        "## Summary",
        ""
    ]
    
    # Count by status
    status_counts = {{}}
    for provider_data in summary['providers'].values():
        status = provider_data['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    report_lines.extend([
        f"- **Fully Working:** {{status_counts.get('FULLY_WORKING', 0)}}",
        f"- **Partially Working (No Pages):** {{status_counts.get('PARTIALLY_WORKING_NO_PAGES', 0)}}",
        f"- **Partially Working (Search Only):** {{status_counts.get('PARTIALLY_WORKING_SEARCH_ONLY', 0)}}",
        f"- **Not Working:** {{status_counts.get('NOT_WORKING', 0)}}",
        "",
        "## Detailed Results",
        "",
        "| Provider | Status | Search | Chapters | Pages | Duration | Last Tested |",
        "|----------|--------|--------|----------|-------|----------|-------------|"
    ])
    
    # Sort providers by status (fully working first)
    status_order = ['FULLY_WORKING', 'PARTIALLY_WORKING_NO_PAGES', 'PARTIALLY_WORKING_SEARCH_ONLY', 'NOT_WORKING']
    sorted_providers = sorted(summary['providers'].items(), 
                            key=lambda x: (status_order.index(x[1]['status']), x[0]))
    
    for provider_name, data in sorted_providers:
        status_emoji = {{
            'FULLY_WORKING': '✅',
            'PARTIALLY_WORKING_NO_PAGES': '⚠️',
            'PARTIALLY_WORKING_SEARCH_ONLY': '⚠️',
            'NOT_WORKING': '❌'
        }}.get(data['status'], '❓')
        
        search_status = '✅' if data['search_success'] else '❌'
        chapters_status = '✅' if data['chapters_success'] else '❌'
        pages_status = '✅' if data['pages_success'] else '❌'
        
        duration = f"{{data.get('test_duration', 0):.1f}}s"
        last_tested = data['last_tested'][:10] if data['last_tested'] else 'Never'
        
        report_lines.append(
            f"| {{provider_name}} | {{status_emoji}} {{data['status'].replace('_', ' ').title()}} | "
            f"{{search_status}} ({{data['search_results']}}) | {{chapters_status}} ({{data['chapters_count']}}) | "
            f"{{pages_status}} ({{data['pages_count']}}) | {{duration}} | {{last_tested}} |"
        )
    
    # Save markdown report
    report_file = results_dir / 'provider_test_report.md'
    with open(report_file, 'w') as f:
        f.write('\\n'.join(report_lines))
    
    print(f"📄 Markdown report generated: {{report_file}}")'''

def generate_test_files():
    """Generate test files for all Phase 4 providers."""
    base_dir = Path(__file__).parent / 'individual_provider_tests'
    base_dir.mkdir(exist_ok=True)
    
    print("🔧 Generating Phase 4 provider test scripts...")
    print("=" * 60)
    
    for provider in PHASE4_PROVIDERS:
        filename = f"test_{provider['name'].lower()}.py"
        filepath = base_dir / filename
        
        # Skip if file already exists
        if filepath.exists():
            print(f"⚠️  Skipping {provider['name']} - file already exists")
            continue
        
        # Generate test content
        test_content = TEST_TEMPLATE.format(
            provider_name=provider['name'],
            description=provider['description']
        )
        
        # Write test file
        with open(filepath, 'w') as f:
            f.write(test_content)
        
        # Make executable
        os.chmod(filepath, 0o755)
        
        print(f"✅ Created test script: {filename}")
    
    print()
    print("📋 Phase 4 Provider Test Scripts Summary:")
    print("-" * 40)
    for provider in PHASE4_PROVIDERS:
        filename = f"test_{provider['name'].lower()}.py"
        status = "✅ Created" if not (base_dir / filename).exists() else "📁 Exists"
        print(f"{status}: {filename} ({provider['description']})")
    
    print()
    print("🚀 Next steps:")
    print("1. Run individual test scripts to generate results")
    print("2. Analyze results for each provider")
    print("3. Investigate and fix any issues found")

if __name__ == "__main__":
    generate_test_files()
