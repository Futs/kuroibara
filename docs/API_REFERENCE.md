# API Reference

## Overview

The Kuroibara API is a RESTful API built with FastAPI, providing comprehensive access to manga search, management, and user functionality. All endpoints are documented with OpenAPI/Swagger.

## Base URLs

- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://yourdomain.com/api/v1`

## Interactive Documentation

- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/openapi.json`

## Authentication

### JWT Token Authentication
```bash
# Login to get access token
POST /api/v1/auth/login
{
  "username": "your_username",
  "password": "your_password"
}

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}

# Use token in subsequent requests
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Refresh Token
```bash
POST /api/v1/auth/refresh
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Core Endpoints

### Search
```bash
# Search manga across all providers
GET /api/v1/search?q={query}&page={page}&limit={limit}&providers={provider_list}

# Parameters:
# - q: Search query (required)
# - page: Page number (default: 1)
# - limit: Results per page (default: 20, max: 100)
# - providers: Comma-separated provider list (optional)
# - nsfw: Include NSFW content (default: false)

# Example
GET /api/v1/search?q=one%20piece&page=1&limit=20&providers=mangadex,mangaplus

# Response
{
  "results": [
    {
      "id": "manga_123",
      "title": "One Piece",
      "author": "Eiichiro Oda",
      "description": "The story follows Monkey D. Luffy...",
      "cover_url": "https://example.com/cover.jpg",
      "provider": "mangadex",
      "status": "ongoing",
      "genres": ["Action", "Adventure", "Comedy"],
      "rating": 9.2,
      "chapters": 1000
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 20,
  "has_next": true
}
```

### Manga Details
```bash
# Get detailed manga information
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
  "last_updated": "2024-01-15T10:30:00Z"
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
      "release_date": "2024-01-15T00:00:00Z",
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
  "created_at": "2024-01-15T10:30:00Z",
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
      "added_at": "2024-01-15T10:30:00Z",
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
      "last_check": "2024-01-15T10:25:00Z",
      "response_time": 1.2,
      "success_rate": 0.98,
      "enabled": true
    },
    {
      "name": "mangaplus",
      "display_name": "MangaPlus",
      "status": "degraded",
      "last_check": "2024-01-15T10:25:00Z",
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
