# External Integrations - Technical Implementation Guide

This document provides technical details for developers working with Kuroibara's external integration system.

## 🏗️ Architecture Overview

### System Components
- **Integration Clients**: Service-specific API clients (Anilist, MAL, Kitsu)
- **Sync Service**: Orchestrates data synchronization between services
- **Database Layer**: Stores integration credentials and manga mappings
- **API Layer**: REST endpoints for frontend integration management
- **Frontend Store**: Pinia store for state management

### Technology Stack
- **Backend**: FastAPI, SQLAlchemy (async), PostgreSQL
- **Frontend**: Vue.js 3, Pinia, Axios
- **Authentication**: OAuth2 (Authorization Code, PKCE, Password Credentials)
- **Database**: PostgreSQL with UUID primary keys

## 📊 Database Schema

### External Integrations Table
```sql
CREATE TABLE external_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    integration_type VARCHAR(50) NOT NULL,
    client_id VARCHAR(255),
    client_secret VARCHAR(255),
    access_token TEXT,
    refresh_token TEXT,
    external_user_id VARCHAR(255),
    external_username VARCHAR(255),
    token_expires_at TIMESTAMP,
    sync_enabled BOOLEAN DEFAULT true,
    sync_reading_progress BOOLEAN DEFAULT true,
    sync_ratings BOOLEAN DEFAULT true,
    sync_status BOOLEAN DEFAULT true,
    auto_sync BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMP,
    last_sync_status VARCHAR(50) DEFAULT 'pending',
    settings JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, integration_type)
);
```

### External Manga Mappings Table
```sql
CREATE TABLE external_manga_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_id UUID NOT NULL REFERENCES external_integrations(id) ON DELETE CASCADE,
    manga_id UUID NOT NULL REFERENCES manga(id) ON DELETE CASCADE,
    external_manga_id VARCHAR(255) NOT NULL,
    external_title VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(integration_id, manga_id),
    UNIQUE(integration_id, external_manga_id)
);
```

## 🔧 Backend Implementation

### Integration Types Enum
```python
class IntegrationType(str, Enum):
    ANILIST = "anilist"
    MYANIMELIST = "myanimelist"
    KITSU = "kitsu"
```

### Base Integration Client
```python
class BaseIntegrationClient(ABC):
    @abstractmethod
    async def authenticate(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate with the external service."""
        pass
    
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh the access token."""
        pass
    
    @abstractmethod
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information."""
        pass
    
    @abstractmethod
    async def get_manga_list(self, access_token: str, **kwargs) -> List[Dict[str, Any]]:
        """Get user's manga list."""
        pass
    
    @abstractmethod
    async def update_manga_status(self, access_token: str, manga_id: str, 
                                status: str, **kwargs) -> bool:
        """Update manga status."""
        pass
    
    @abstractmethod
    async def search_manga(self, access_token: str, query: str, 
                         limit: int = 10) -> List[Dict[str, Any]]:
        """Search for manga."""
        pass
```

### Service-Specific Implementations

#### Anilist Client
- **Authentication**: OAuth2 Authorization Code Flow
- **API Base URL**: `https://graphql.anilist.co`
- **Rate Limiting**: 90 requests per minute
- **Special Features**: GraphQL API, comprehensive metadata

#### MyAnimeList Client
- **Authentication**: OAuth2 with PKCE
- **API Base URL**: `https://api.myanimelist.net/v2`
- **Rate Limiting**: Varies by endpoint
- **Special Features**: Extensive community data, detailed statistics

#### Kitsu Client
- **Authentication**: OAuth2 Resource Owner Password Credentials
- **API Base URL**: `https://kitsu.io/api/edge`
- **Rate Limiting**: Standard rate limits
- **Special Features**: JSON:API format, 20-point rating scale

## 🔄 Sync Service

### Sync Process Flow
1. **Validation**: Check integration status and tokens
2. **Token Refresh**: Refresh expired tokens if possible
3. **Data Retrieval**: Fetch manga list from external service
4. **Mapping**: Map external manga to internal manga records
5. **Conflict Resolution**: Handle conflicts using timestamps
6. **Update**: Apply changes to local database
7. **Push Changes**: Send local changes to external service

### Sync Strategies
- **Full Sync**: Complete library synchronization
- **Incremental Sync**: Only sync changes since last sync
- **Manual Sync**: User-triggered synchronization
- **Auto Sync**: Triggered by local changes

## 🌐 API Endpoints

### Integration Management
```python
# Get integration settings
GET /api/v1/integrations/settings
Response: {
    "anilist": {...},
    "myanimelist": {...},
    "kitsu": {...}
}

# Setup integration credentials
POST /api/v1/integrations/setup
Body: {
    "integration_type": "anilist",
    "client_id": "...",
    "client_secret": "..."
}

# Update integration settings
PUT /api/v1/integrations/{integration_type}
Body: {
    "sync_enabled": true,
    "auto_sync": false,
    "sync_ratings": true
}
```

### Service Connection
```python
# Connect Anilist
POST /api/v1/integrations/anilist/connect
Body: {
    "authorization_code": "...",
    "redirect_uri": "..."
}

# Connect MyAnimeList
POST /api/v1/integrations/myanimelist/connect
Body: {
    "authorization_code": "...",
    "code_verifier": "...",
    "redirect_uri": "..."
}

# Connect Kitsu
POST /api/v1/integrations/kitsu/connect
Body: {
    "username": "...",
    "password": "..."
}
```

### Sync Operations
```python
# Trigger manual sync
POST /api/v1/integrations/sync
Body: {
    "integration_type": "anilist",
    "force_full_sync": false
}

# Disconnect integration
DELETE /api/v1/integrations/{integration_type}
```

## 🎨 Frontend Implementation

### Pinia Store Structure
```javascript
export const useIntegrationsStore = defineStore("integrations", {
  state: () => ({
    anilistStatus: null,
    malStatus: null,
    kitsuStatus: null,
    loading: false,
    error: null,
    syncInProgress: false,
  }),

  getters: {
    isAnilistConnected: (state) => state.anilistStatus?.is_connected || false,
    isMALConnected: (state) => state.malStatus?.is_connected || false,
    isKitsuConnected: (state) => state.kitsuStatus?.is_connected || false,
    hasAnyConnection: (state) => /* ... */,
  },

  actions: {
    async fetchIntegrationSettings() { /* ... */ },
    async connectAnilist(authCode, redirectUri) { /* ... */ },
    async connectMAL(authCode, codeVerifier, redirectUri) { /* ... */ },
    async connectKitsu(credentials) { /* ... */ },
    async triggerSync(integrationType) { /* ... */ },
    async disconnectIntegration(integrationType) { /* ... */ },
  }
});
```

### OAuth Callback Handling
```javascript
// Anilist callback
router.get('/integrations/anilist/callback', (to) => {
  const authCode = to.query.code;
  const redirectUri = `${window.location.origin}/integrations/anilist/callback`;
  return integrationsStore.handleAnilistCallback(authCode, redirectUri);
});

// MyAnimeList callback
router.get('/integrations/mal/callback', (to) => {
  const authCode = to.query.code;
  const codeVerifier = sessionStorage.getItem('mal_code_verifier');
  const redirectUri = `${window.location.origin}/integrations/mal/callback`;
  return integrationsStore.handleMALCallback(authCode, codeVerifier, redirectUri);
});
```

## 🔒 Security Considerations

### Token Management
- Access tokens stored encrypted in database
- Refresh tokens used for automatic token renewal
- Tokens expire and are refreshed automatically
- Client secrets never exposed to frontend

### API Security
- All endpoints require user authentication
- Rate limiting implemented per service requirements
- Input validation on all API endpoints
- CORS properly configured for OAuth redirects

### Data Privacy
- Only necessary permissions requested from external services
- User data never shared between services
- Sync can be disabled without losing connection
- Users can disconnect services at any time

## 🧪 Testing

### Unit Tests
- Integration client methods
- Sync service logic
- API endpoint responses
- Database operations

### Integration Tests
- OAuth flows (mocked)
- Sync process end-to-end
- Error handling scenarios
- Token refresh mechanisms

### Frontend Tests
- Component rendering
- Store state management
- User interaction flows
- Error state handling

## 📈 Performance Optimization

### Caching Strategy
- Integration status cached in frontend store
- API responses cached with appropriate TTL
- Database queries optimized with indexes
- Batch operations for bulk sync

### Rate Limiting
- Respect external service rate limits
- Implement exponential backoff for retries
- Queue sync operations to prevent conflicts
- Monitor API usage and adjust accordingly

## 🔧 Development Setup

### Environment Configuration
```bash
# Backend environment variables
DATABASE_URL=postgresql://user:pass@localhost/kuroibara
ANILIST_CLIENT_ID=optional_default_client_id
ANILIST_CLIENT_SECRET=optional_default_client_secret
MAL_CLIENT_ID=optional_default_client_id
MAL_CLIENT_SECRET=optional_default_client_secret

# Frontend environment variables
VITE_ANILIST_CLIENT_ID=optional_default_client_id
VITE_MAL_CLIENT_ID=optional_default_client_id
```

### Database Migrations
```bash
# Run migrations
docker compose exec backend alembic upgrade head

# Create new migration
docker compose exec backend alembic revision --autogenerate -m "description"
```

### Testing
```bash
# Run backend tests
docker compose exec backend python -m pytest tests/

# Run frontend tests
docker compose exec frontend npm run test

# Run integration validation
docker compose exec backend python test_integration_validation.py
```

---

*This technical guide provides implementation details for developers. For user-facing documentation, see the External Integrations Guide.*
