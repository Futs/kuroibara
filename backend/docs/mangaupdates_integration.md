# MangaUpdates API Integration

## Overview

This document outlines the integration with MangaUpdates API v1, including rate limiting policies, acceptable use guidelines, and implementation details.

## Official Rate Limiting Policy

Based on communication with MangaUpdates admin:

### Read-Only Operations (No Rate Limiting)
- **GET requests** - Not rate limited
- **Search POST requests** - Not rate limited  
- **Most read-only actions** - Not rate limited
- Only protected by **DDOS protection** (returns 429 errors when triggered)

### Update Operations (Rate Limited)
- **UPDATE operations** - Limited to **1 per 5 seconds**
- Different update types may have slightly different limits
- This applies to data modification operations only

### Error Handling
- **429 errors** indicate DDOS protection triggered, not normal rate limiting
- These are temporary and should be handled gracefully with backoff

## Acceptable Use Policy

From MangaUpdates OpenAPI specification:

### Requirements
1. **Credit MangaUpdates** when using data provided by the API
2. **Use reasonable spacing** between requests (for courtesy, not technical requirement)
3. **Employ caching mechanisms** when accessing data
4. **Do NOT use** MangaUpdates data or API to:
   - Deceive or defraud users
   - Assist or perform illegal actions
   - Create spam
   - Damage the database

### Warranties
- MangaUpdates makes **no warranties** about service availability or data correctness
- Service provided **as-is** and may change at any time

## Implementation Details

### API Endpoint
- **Base URL**: `https://api.mangaupdates.com/v1`
- **Search Endpoint**: `/series/search` (POST)
- **Authentication**: Not required for search operations

### Request Format
```json
{
  "search": "manga title",
  "page": 1,
  "perpage": 25,
  "stype": "title"
}
```

### Response Format
```json
{
  "total_hits": 1234,
  "page": 1,
  "per_page": 25,
  "results": [
    {
      "record": {
        "series_id": 12345,
        "title": "Manga Title",
        "url": "https://www.mangaupdates.com/series/...",
        "description": "Description text",
        "image": {
          "url": {
            "original": "https://cdn.mangaupdates.com/image/...",
            "thumb": "https://cdn.mangaupdates.com/image/thumb/..."
          },
          "height": 250,
          "width": 158
        },
        "type": "Manga",
        "year": "2023",
        "bayesian_rating": 8.5,
        "rating_votes": 1000,
        "genres": [
          {"genre": "Action"},
          {"genre": "Adventure"}
        ]
      },
      "hit_title": "Matched Title",
      "metadata": {
        "user_list": {...},
        "user_genre_highlights": []
      }
    }
  ]
}
```

## Kuroibara Implementation

### Rate Limiting Strategy
- **No rate limiting** for search operations (per admin guidance)
- **5-second intervals** for any future update operations
- **Caching** implemented with 5-minute TTL for efficiency
- **429 error handling** with appropriate logging

### Headers
```http
Content-Type: application/json
User-Agent: Kuroibara/1.0 (Manga Library Manager; https://github.com/Futs/kuroibara)
```

### Data Mapping
- **Title**: `record.title`
- **Description**: `record.description`
- **Cover Image**: `record.image.url.original`
- **Type**: `record.type` (string)
- **Year**: `record.year` (string)
- **Rating**: `record.bayesian_rating`
- **Rating Count**: `record.rating_votes`
- **Genres**: `record.genres[].genre`
- **NSFW Detection**: Based on genres (Adult, Hentai, etc.)

### Confidence Scoring
- **Primary tier** indexer (highest priority)
- **Confidence score**: 1.0 for all results (authoritative source)
- **Fallback**: Other indexers used when MangaUpdates unavailable

## Error Handling

### HTTP Status Codes
- **200**: Success
- **400**: Validation or service error
- **429**: DDOS protection triggered (temporary)
- **500**: Server error (temporary)

### Retry Strategy
- **429 errors**: Log warning, return empty results (don't retry immediately)
- **500 errors**: Log error, return empty results
- **Network errors**: Log error, return empty results
- **Parsing errors**: Log error, skip individual results

## Testing

### Connection Test
```python
async with MangaUpdatesIndexer() as indexer:
    success, message = await indexer.test_connection()
```

### Search Test
```python
async with MangaUpdatesIndexer() as indexer:
    results = await indexer.search("naruto", limit=10)
```

### Expected Results
- **Connection**: Should return `True` with success message
- **Search**: Should return list of `UniversalMetadata` objects
- **NSFW Detection**: Should correctly identify adult content
- **Performance**: No artificial delays for search operations

## Monitoring

### Health Checks
- Regular connection tests
- Response time monitoring
- Error rate tracking
- DDOS protection trigger frequency

### Metrics
- Search success rate
- Average response time
- Cache hit rate
- NSFW detection accuracy

## Future Considerations

### Potential Enhancements
1. **Series Details**: Implement detailed series information retrieval
2. **Author Search**: Add author-specific search capabilities
3. **Genre Filtering**: Implement advanced genre-based filtering
4. **Update Operations**: If needed, implement with proper 5-second rate limiting

### API Changes
- Monitor MangaUpdates announcements for API changes
- Update implementation as needed
- Maintain backward compatibility where possible

## Contact Information

For API-related questions:
- lambchopsil@mangaupdates.com
- manick@mangaupdates.com

## References

- [MangaUpdates API Documentation](https://api.mangaupdates.com/v1/docs)
- [OpenAPI Specification](https://api.mangaupdates.com/v1/openapi.yaml)
- [MangaUpdates Website](https://www.mangaupdates.com)
