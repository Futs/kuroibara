# Kuroibara API Reference

This document provides a comprehensive reference for all Kuroibara API endpoints, including request/response schemas, authentication requirements, and usage examples.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
All endpoints require JWT authentication unless otherwise specified.

```http
Authorization: Bearer <jwt_token>
```

---

## API Endpoint Architecture

```mermaid
graph TB
    %% API Gateway
    Client[🌐 Client] --> Gateway[⚡ FastAPI Gateway]
    Gateway --> Auth[🔐 JWT Middleware]

    %% API Router Groups
    Auth --> APIv1[🛣️ API Router v1]
    APIv1 --> AuthGroup[🔐 Authentication]
    APIv1 --> SearchGroup[🔍 Enhanced Search]
    APIv1 --> LibraryGroup[📚 Library Management]
    APIv1 --> TorrentGroup[🌸 Torrent Operations]
    APIv1 --> HealthGroup[💚 Health Monitoring]
    APIv1 --> UserGroup[👤 User Management]
    APIv1 --> DownloadGroup[📥 Download Management]

    %% Authentication Endpoints
    AuthGroup --> Login[POST /auth/login]
    AuthGroup --> Register[POST /auth/register]
    AuthGroup --> Refresh[POST /auth/refresh]
    AuthGroup --> Logout[POST /auth/logout]

    %% Search Endpoints
    SearchGroup --> EnhancedSearch[POST /search/enhanced]
    SearchGroup --> AddFromMU[POST /search/enhanced/add-from-mangaupdates]
    SearchGroup --> TestIndexer[POST /search/enhanced/test-indexer]

    %% Library Endpoints
    LibraryGroup --> GetLibrary[GET /library/]
    LibraryGroup --> AddManga[POST /library/add]
    LibraryGroup --> UpdateManga[PUT /library/{id}]
    LibraryGroup --> DeleteManga[DELETE /library/{id}]
    LibraryGroup --> GetDownloads[GET /library/downloads]

    %% Torrent Endpoints
    TorrentGroup --> SearchTorrents[GET /torrents/search]
    TorrentGroup --> DownloadTorrent[POST /torrents/download]
    TorrentGroup --> ListIndexers[GET /torrents/indexers]
    TorrentGroup --> IndexerHealth[GET /torrents/indexers/health]

    %% Health Endpoints
    HealthGroup --> SystemHealth[GET /health/]
    HealthGroup --> IndexerHealthCheck[GET /health/indexers]
    HealthGroup --> QuickHealth[GET /health/quick]

    classDef authEndpoint fill:#e3f2fd
    classDef searchEndpoint fill:#f1f8e9
    classDef libraryEndpoint fill:#fff3e0
    classDef torrentEndpoint fill:#fce4ec
    classDef healthEndpoint fill:#e8f5e8

    class Login,Register,Refresh,Logout authEndpoint
    class EnhancedSearch,AddFromMU,TestIndexer searchEndpoint
    class GetLibrary,AddManga,UpdateManga,DeleteManga libraryEndpoint
    class SearchTorrents,DownloadTorrent,ListIndexers torrentEndpoint
    class SystemHealth,IndexerHealthCheck,QuickHealth healthEndpoint
```

---

## Authentication Endpoints

### POST /auth/login
Authenticate user and receive JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "username": "user123",
    "is_active": true
  }
}
```

### POST /auth/register
Register new user account.

**Request:**
```json
{
  "email": "newuser@example.com",
  "username": "newuser",
  "password": "securepassword123"
}
```

---

## Enhanced Search Endpoints

### POST /search/enhanced
Perform tiered search across multiple providers.

**Request:**
```json
{
  "query": "solo leveling",
  "limit": 25,
  "include_nsfw": false,
  "providers": ["mangaupdates", "madaradx", "mangadx"]
}
```

**Response:**
```json
{
  "query": "solo leveling",
  "total_results": 15,
  "search_time_ms": 1250,
  "results": [
    {
      "title": "Solo Leveling",
      "description": "10 years ago, after \"the Gate\"...",
      "cover_image": "https://example.com/cover.jpg",
      "provider": "enhanced_mangaupdates",
      "url": "https://mangaupdates.com/series/123",
      "type": "manhwa",
      "status": "completed",
      "year": 2018,
      "rating": 9.2,
      "genres": ["Action", "Adventure", "Fantasy"],
      "is_nsfw": false,
      "in_library": false,
      "confidence_score": 0.95,
      "source_tier": "primary"
    }
  ],
  "provider_stats": {
    "mangaupdates": {"results": 8, "response_time_ms": 450},
    "madaradx": {"results": 5, "response_time_ms": 600},
    "mangadx": {"results": 2, "response_time_ms": 200}
  }
}
```

### POST /search/enhanced/add-from-mangaupdates
Add manga to library from MangaUpdates search result.

**Request:**
```json
{
  "mu_entry_id": "54572530979",
  "title": "Solo Leveling",
  "cover_image": "https://example.com/cover.jpg"
}
```

---

## Library Management Endpoints

### GET /library/
Retrieve user's manga library with filtering and pagination.

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Results per page (default: 20)
- `status`: Filter by reading status
- `search`: Search within library
- `sort`: Sort field (title, added_at, rating)
- `order`: Sort order (asc, desc)

**Response:**
```json
{
  "total": 150,
  "page": 1,
  "limit": 20,
  "pages": 8,
  "manga": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Solo Leveling",
      "description": "10 years ago, after \"the Gate\"...",
      "cover_image": "https://example.com/cover.jpg",
      "status": "completed",
      "type": "manhwa",
      "year": 2018,
      "is_nsfw": false,
      "user_status": "reading",
      "user_rating": 9.0,
      "chapters_count": 179,
      "last_read_chapter": 45,
      "added_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-20T15:45:00Z"
    }
  ]
}
```

### POST /library/add
Add manga to user's library.

**Request:**
```json
{
  "title": "Solo Leveling",
  "description": "10 years ago, after \"the Gate\"...",
  "cover_image": "https://example.com/cover.jpg",
  "type": "manhwa",
  "status": "completed",
  "year": 2018,
  "genres": ["Action", "Adventure", "Fantasy"],
  "mangaupdates_id": "54572530979"
}
```

---

## Torrent Operations Endpoints

### GET /torrents/search
Search for torrents across configured indexers.

**Query Parameters:**
- `query`: Search query (required)
- `category`: Torrent category (manga, anime, all)
- `indexer`: Specific indexer to search
- `limit`: Maximum results per indexer (default: 50)

**Response:**
```json
{
  "query": "solo leveling",
  "category": "manga",
  "total_results": 25,
  "indexer_results": {
    "nyaa": [
      {
        "title": "[Yen Press] Solo Leveling Vol. 1-8 (Digital)",
        "magnet_link": "magnet:?xt=urn:btih:...",
        "torrent_url": "https://nyaa.si/download/123456.torrent",
        "size": "2.1 GB",
        "size_bytes": 2254857830,
        "seeders": 45,
        "leechers": 12,
        "upload_date": "2024-01-15T10:30:00Z",
        "category": "Literature - English-translated",
        "indexer": "Nyaa",
        "info_hash": "A1B2C3D4E5F6789012345678901234567890ABCD"
      }
    ]
  }
}
```

### POST /torrents/download
Download a torrent using configured download client.

**Request:**
```json
{
  "title": "[Yen Press] Solo Leveling Vol. 1-8 (Digital)",
  "manga_id": "123e4567-e89b-12d3-a456-426614174000",
  "client_id": "456e7890-e89b-12d3-a456-426614174000",
  "magnet_link": "magnet:?xt=urn:btih:...",
  "indexer": "nyaa",
  "info_hash": "A1B2C3D4E5F6789012345678901234567890ABCD",
  "size": "2.1 GB",
  "seeders": 45,
  "leechers": 12
}
```

---

## Health Monitoring Endpoints

### GET /health/
Comprehensive system health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1705320600,
  "summary": {
    "response_time_ms": 125,
    "health_percentage": 95
  },
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15,
      "message": "Connected to PostgreSQL"
    },
    "cache": {
      "status": "healthy",
      "response_time_ms": 5,
      "message": "Connected to Valkey"
    },
    "indexers": {
      "status": "degraded",
      "healthy_count": 2,
      "total_count": 3,
      "message": "MadaraDx temporarily unavailable"
    },
    "providers": {
      "status": "healthy",
      "enabled_count": 3,
      "total_count": 3,
      "message": "All providers operational"
    }
  }
}
```

### GET /health/indexers
Detailed health status of search indexers.

**Response:**
```json
{
  "status": "healthy",
  "healthy_count": 3,
  "total_count": 3,
  "response_time_ms": 450,
  "indexers": {
    "mangaupdates": {
      "status": "healthy",
      "tier": "primary",
      "response_time_ms": 380,
      "last_check": "2024-01-15T10:30:00Z",
      "message": "API responding normally"
    },
    "madaradx": {
      "status": "healthy",
      "tier": "secondary",
      "response_time_ms": 520,
      "last_check": "2024-01-15T10:30:00Z",
      "message": "Web scraping operational"
    },
    "mangadx": {
      "status": "healthy",
      "tier": "tertiary",
      "response_time_ms": 450,
      "last_check": "2024-01-15T10:30:00Z",
      "message": "API responding normally"
    }
  }
}
```

---

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/v1/auth/login"
}
```

### Common Error Codes
- `AUTHENTICATION_REQUIRED`: Missing or invalid JWT token
- `VALIDATION_ERROR`: Request validation failed
- `NOT_FOUND`: Requested resource not found
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `EXTERNAL_SERVICE_ERROR`: Third-party service unavailable
- `INTERNAL_SERVER_ERROR`: Unexpected server error

---

## Rate Limiting

API endpoints are rate-limited to ensure fair usage:

- **Authentication**: 5 requests per minute
- **Search**: 30 requests per minute
- **Library**: 60 requests per minute
- **Health**: 10 requests per minute

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
X-RateLimit-Reset: 1705320660
```
GET /api/v1/manga/{manga_id}

# Response
{
  "id": "manga_123",
  "title": "One Piece",
  "alternative_titles": ["ワンピース"],
  "author": "Eiichiro Oda",
  "artist": "Eiichiro Oda",
  "description": "The story follows Monkey D. Luffy...",
  "cover_url": "https://example.com/cover.jpg",
  "banner_url": "https://example.com/banner.jpg",
  "provider": "mangadex",
  "provider_id": "32d76d19-8a05-4db0-9fc2-e0b0648fe9d0",
  "status": "ongoing",
  "genres": ["Action", "Adventure", "Comedy"],
  "tags": ["Pirates", "Superpowers", "Friendship"],
  "rating": 9.2,
  "chapters": 1000,
  "volumes": 100,
  "year": 1997,
  "nsfw": false,
  "last_updated": "2025-01-15T10:30:00Z"
}
```

### Chapter Management
```bash
# Get chapter list for a manga
GET /api/v1/manga/{manga_id}/chapters?page={page}&limit={limit}

# Response
{
  "chapters": [
    {
      "id": "chapter_456",
      "number": "1001",
      "title": "The New Era",
      "volume": "100",
      "pages": 20,
      "release_date": "2025-01-15T00:00:00Z",
      "scanlator": "TCBScans",
      "language": "en"
    }
  ],
  "total": 1000,
  "page": 1,
  "limit": 50
}

# Get chapter images
GET /api/v1/chapters/{chapter_id}/images

# Response
{
  "images": [
    "https://example.com/chapter/page_001.jpg",
    "https://example.com/chapter/page_002.jpg",
    "https://example.com/chapter/page_003.jpg"
  ],
  "total_pages": 20
}
```

## User Management

### User Registration
```bash
POST /api/v1/auth/register
{
  "username": "new_user",
  "email": "user@example.com",
  "password": "secure_password123",
  "confirm_password": "secure_password123"
}

# Response
{
  "id": "user_789",
  "username": "new_user",
  "email": "user@example.com",
  "created_at": "2025-01-15T10:30:00Z",
  "is_active": true,
  "is_verified": false
}
```

### User Profile
```bash
# Get current user profile
GET /api/v1/user/profile

# Update user profile
PATCH /api/v1/user/profile
{
  "display_name": "My Display Name",
  "bio": "Manga enthusiast",
  "avatar_url": "https://example.com/avatar.jpg",
  "preferences": {
    "nsfw_content": false,
    "default_language": "en",
    "reading_direction": "ltr"
  }
}
```

### Favorites Management
```bash
# Add manga to favorites
POST /api/v1/favorites/{manga_id}

# Remove from favorites
DELETE /api/v1/favorites/{manga_id}

# Get user favorites
GET /api/v1/favorites?page={page}&limit={limit}&sort={sort_by}

# Response
{
  "favorites": [
    {
      "manga": {
        "id": "manga_123",
        "title": "One Piece",
        "cover_url": "https://example.com/cover.jpg",
        "status": "ongoing"
      },
      "added_at": "2025-01-15T10:30:00Z",
      "last_read_chapter": "1000",
      "reading_progress": 0.95
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 20
}
```

## Provider Management

### Provider Status
```bash
# Get all provider health status
GET /api/v1/providers/status

# Response
{
  "providers": [
    {
      "name": "mangadex",
      "display_name": "MangaDex",
      "status": "healthy",
      "last_check": "2025-01-15T10:25:00Z",
      "response_time": 1.2,
      "success_rate": 0.98,
      "enabled": true
    },
    {
      "name": "mangaplus",
      "display_name": "MangaPlus",
      "status": "degraded",
      "last_check": "2025-01-15T10:25:00Z",
      "response_time": 3.5,
      "success_rate": 0.85,
      "enabled": true
    }
  ]
}

# Get specific provider status
GET /api/v1/providers/{provider_name}/status
```

### Provider Configuration (Admin Only)
```bash
# Update provider settings
PATCH /api/v1/admin/providers/{provider_name}
{
  "enabled": true,
  "priority": 1,
  "rate_limit": 10,
  "timeout": 30
}
```

## Admin Endpoints

### User Management (Admin Only)
```bash
# Get all users
GET /api/v1/admin/users?page={page}&limit={limit}&search={query}

# Update user status
PATCH /api/v1/admin/users/{user_id}
{
  "is_active": true,
  "is_verified": true,
  "role": "user"
}

# Delete user
DELETE /api/v1/admin/users/{user_id}
```

### System Statistics
```bash
# Get system statistics
GET /api/v1/admin/stats

# Response
{
  "users": {
    "total": 1250,
    "active": 1100,
    "new_today": 15
  },
  "manga": {
    "total": 50000,
    "favorites": 125000,
    "searches_today": 5000
  },
  "providers": {
    "total": 25,
    "healthy": 22,
    "degraded": 2,
    "unhealthy": 1
  }
}
```

## Error Handling

### HTTP Status Codes
- **200 OK** - Request successful
- **201 Created** - Resource created successfully
- **400 Bad Request** - Invalid request parameters
- **401 Unauthorized** - Authentication required
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource not found
- **422 Unprocessable Entity** - Validation error
- **429 Too Many Requests** - Rate limit exceeded
- **500 Internal Server Error** - Server error

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

## Rate Limiting

### Default Limits
- **Anonymous users**: 100 requests per hour
- **Authenticated users**: 1000 requests per hour
- **Premium users**: 5000 requests per hour
- **Admin users**: No limit

### Rate Limit Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642262400
```

## Pagination

### Standard Pagination
```bash
GET /api/v1/endpoint?page=1&limit=20

# Response includes pagination metadata
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

## WebSocket Endpoints

### Real-time Updates
```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket('ws://localhost:8000/api/v1/ws');

// Subscribe to provider status updates
ws.send(JSON.stringify({
  "type": "subscribe",
  "channel": "provider_status"
}));

// Receive updates
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Provider status update:', data);
};
```

## SDK Examples

### Python SDK
```python
import requests

class KuroibaraAPI:
    def __init__(self, base_url, token=None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({
                'Authorization': f'Bearer {token}'
            })
    
    def search(self, query, page=1, limit=20):
        response = self.session.get(
            f'{self.base_url}/search',
            params={'q': query, 'page': page, 'limit': limit}
        )
        return response.json()
    
    def get_manga(self, manga_id):
        response = self.session.get(f'{self.base_url}/manga/{manga_id}')
        return response.json()

# Usage
api = KuroibaraAPI('http://localhost:8000/api/v1', token='your_token')
results = api.search('one piece')
```

### JavaScript SDK
```javascript
class KuroibaraAPI {
  constructor(baseUrl, token = null) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers
    });

    return response.json();
  }

  async search(query, page = 1, limit = 20) {
    const params = new URLSearchParams({ q: query, page, limit });
    return this.request(`/search?${params}`);
  }

  async getManga(mangaId) {
    return this.request(`/manga/${mangaId}`);
  }
}

// Usage
const api = new KuroibaraAPI('http://localhost:8000/api/v1', 'your_token');
const results = await api.search('one piece');
```
