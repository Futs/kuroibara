# JavaScript Provider Implementation

## Overview

This document describes the implementation of the new `JavaScriptProvider` base class and the `HiperDexProvider` that extends it. This architecture provides a robust foundation for handling modern manga sites that use heavy JavaScript, dynamic content loading, and bot protection.

## Architecture

### JavaScriptProvider Base Class

**Location**: `kuroibara/backend/app/core/providers/javascript_provider.py`

The `JavaScriptProvider` is an abstract base class that extends `BaseProvider` with advanced capabilities for JavaScript-heavy sites:

#### Key Features:
- **FlareSolverr Integration**: Automatic Cloudflare bypass using FlareSolverr
- **Session Management**: Cookie persistence and session handling
- **Rate Limiting**: Conservative rate limiting (3+ seconds between requests)
- **Browser Simulation**: Rotating user agents and realistic headers
- **JavaScript Extraction**: Parse JavaScript variables and JSON data
- **Retry Logic**: Exponential backoff for failed requests
- **Bot Protection Detection**: Automatic detection of protection mechanisms

#### Core Methods:
- `_make_request()`: Enhanced HTTP requests with JS execution support
- `_apply_rate_limit()`: Conservative rate limiting for JS sites
- `_get_headers()`: Browser simulation with rotating user agents
- `_extract_javascript_data()`: Extract data from JavaScript variables
- `health_check()`: Enhanced health checking with bot protection detection

### HiperDexProvider Implementation

**Location**: `kuroibara/backend/app/core/providers/hiperdex.py`

The `HiperDexProvider` extends `JavaScriptProvider` to handle HiperDEX specifically:

#### Site Characteristics:
- **Base URL**: https://hiperdex.com
- **Framework**: WordPress with Madara theme + JavaScript enhancements
- **Content Type**: NSFW manga/manhwa
- **Protection**: Moderate bot protection, JavaScript-based content loading
- **CDN**: Uses `mdg.hiperdex.com` for image hosting

#### Implementation Details:
- **Search**: WordPress search with post_type=wp-manga
- **Selectors**: Comprehensive CSS selectors for content extraction
- **JavaScript Patterns**: Regex patterns for extracting JS variables
- **Image Handling**: CDN-aware image URL extraction
- **NSFW Support**: Full NSFW content classification

## Configuration

### Provider Registration

**File**: `kuroibara/backend/app/core/providers/config/providers_default.json`

```json
{
  "id": "hiperdex",
  "name": "HiperDEX",
  "class_name": "HiperDexProvider",
  "supports_nsfw": true,
  "priority": 10,
  "use_flaresolverr": true,
  "requires_flaresolverr": false,
  "params": {
    "supports_nsfw": true,
    "use_flaresolverr": true
  }
}
```

### Rate Limiting Configuration

**File**: `kuroibara/frontend/app/src/config/providerRateLimits.js`

```javascript
hiperdex: {
  limit: 20, // 20 requests per minute (3 second intervals)
  windowMs: 60000,
  burstLimit: 2,
  retryAfter: 3000,
  description: "HiperDEX requires conservative rate limiting due to JavaScript content and bot protection",
},
```

### Download Settings

```javascript
hiperdex: {
  maxConcurrentDownloads: 1, // Conservative for JavaScript-heavy site
  chapterDelay: 3000, // 3 seconds between chapters
  pageDelay: 1000, // 1 second between pages
  retryAttempts: 3,
  timeout: 60000, // Longer timeout for JavaScript execution
},
```

## Factory Integration

**File**: `kuroibara/backend/app/core/agents/factory.py`

The factory has been updated to:
1. Import both `JavaScriptProvider` and `HiperDexProvider`
2. Register both classes in the provider registry
3. Handle special initialization for `HiperDexProvider`

## Benefits of This Architecture

### 1. **Future-Proofing**
- Template for other JavaScript-heavy sites (Webtoons, Tapas, etc.)
- Centralized bot protection handling
- Reusable session management

### 2. **Scalability**
- Easy to add new JavaScript-based providers
- Shared rate limiting and retry logic
- Common browser simulation techniques

### 3. **Robustness**
- Multiple fallback mechanisms (FlareSolverr → direct requests)
- Comprehensive error handling
- Adaptive rate limiting

### 4. **Maintainability**
- Clear separation of concerns
- Documented selector patterns
- Configurable JavaScript extraction

## Testing

**Test Script**: `kuroibara/backend/scripts/test_hiperdex.py`

The test script validates:
- Provider initialization
- Health checking
- Search functionality
- Manga details extraction
- Chapter list retrieval
- Page URL extraction
- JavaScript data parsing

## Usage Examples

### Basic Provider Usage

```python
from app.core.providers.hiperdex import HiperDexProvider

# Initialize provider
provider = HiperDexProvider()

# Search for manga
results = await provider.search("Stupidemic")

# Get manga details
details = await provider.get_manga_details(results[0]['url'])

# Get chapters
chapters = await provider.get_chapters(details['url'])

# Get pages
pages = await provider.get_pages(chapters[0]['url'])
```

### Creating New JavaScript Providers

```python
from app.core.providers.javascript_provider import JavaScriptProvider

class NewSiteProvider(JavaScriptProvider):
    def __init__(self):
        super().__init__(
            name="NewSite",
            url="https://newsite.com",
            supports_nsfw=True,
            selectors={
                'search_results': '.manga-item',
                'pages': 'img[src*="cdn.newsite.com"]'
            },
            javascript_patterns={
                'chapter_data': r'var\s+chapterData\s*=\s*({[^}]+})'
            }
        )
    
    async def search(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        # Implement site-specific search logic
        pass
```

## Performance Considerations

### Rate Limiting
- **Conservative by default**: 3-second intervals between requests
- **Burst protection**: Maximum 2 requests per second
- **Adaptive delays**: Exponential backoff on failures

### Resource Usage
- **Session reuse**: Persistent cookies and headers
- **Connection pooling**: Efficient HTTP client usage
- **Memory management**: Cleanup of large response objects

### Error Handling
- **Graceful degradation**: Fallback from FlareSolverr to direct requests
- **Retry logic**: Up to 3 retries with increasing delays
- **Timeout management**: Longer timeouts for JavaScript execution

## Security Considerations

### Bot Protection Bypass
- **FlareSolverr integration**: Handles Cloudflare and similar protections
- **Browser simulation**: Realistic headers and user agents
- **Session persistence**: Maintains authentication state

### Rate Limiting Compliance
- **Respectful crawling**: Conservative request rates
- **Provider-specific limits**: Tailored to each site's requirements
- **Burst protection**: Prevents overwhelming target servers

## Future Enhancements

### Planned Features
1. **Proxy rotation**: Support for multiple proxy servers
2. **CAPTCHA solving**: Integration with CAPTCHA solving services
3. **Advanced JavaScript execution**: Full browser automation with Selenium
4. **Content caching**: Local caching of frequently accessed content
5. **Analytics**: Provider performance monitoring and optimization

### Potential New Providers
- **Webtoons**: Official webtoon platform
- **Tapas**: Independent comic platform
- **Official publishers**: Sites with heavy protection
- **Modern aggregators**: React/Vue-based manga sites

This architecture provides a solid foundation for handling the increasingly complex landscape of modern manga sites while maintaining the reliability and performance standards of the Kuroibara project.
