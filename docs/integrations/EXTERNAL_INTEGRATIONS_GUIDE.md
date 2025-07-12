# External Integrations Guide

Kuroibara supports seamless integration with popular manga tracking services, allowing you to sync your reading progress, ratings, and manga lists across platforms.

## 🔗 Supported Services

### Anilist
- **Type**: Anime and manga tracking platform
- **Authentication**: OAuth2 Authorization Code Flow
- **Features**: Reading progress, ratings, status tracking, comprehensive manga database
- **Website**: [anilist.co](https://anilist.co)

### MyAnimeList (MAL)
- **Type**: Anime and manga database and tracking service
- **Authentication**: OAuth2 with PKCE (Proof Key for Code Exchange)
- **Features**: Reading progress, ratings, status tracking, extensive community features
- **Website**: [myanimelist.net](https://myanimelist.net)

### Kitsu
- **Type**: Anime and manga tracking platform
- **Authentication**: Username/Password (OAuth2 Resource Owner Password Credentials)
- **Features**: Reading progress, ratings (20-point scale), status tracking, modern interface
- **Website**: [kitsu.io](https://kitsu.io)

## 🚀 Getting Started

### Accessing Integration Settings

1. Navigate to **Settings** in the main menu
2. Click on the **Integrations** tab
3. Choose the service you want to connect

### Setting Up API Credentials

#### Option 1: Environment Variables (Optional)
You can pre-configure API credentials using environment variables:

```bash
# Anilist
ANILIST_CLIENT_ID=your_anilist_client_id
ANILIST_CLIENT_SECRET=your_anilist_client_secret

# MyAnimeList
MAL_CLIENT_ID=your_mal_client_id
MAL_CLIENT_SECRET=your_mal_client_secret

# Kitsu (optional - uses direct authentication)
# No API credentials needed for basic usage
```

#### Option 2: UI Configuration (Recommended)
Configure credentials directly through the web interface for easier management.

## 📋 Service-Specific Setup

### Anilist Integration

#### Getting API Credentials
1. Visit [Anilist Developer Settings](https://anilist.co/settings/developer)
2. Create a new application
3. Set redirect URI to: `http://your-domain:3000/integrations/anilist/callback`
4. Copy the Client ID and Client Secret

#### Connection Process
1. Enter your Client ID and Client Secret (or use environment variables)
2. Click "Connect Anilist"
3. Authorize Kuroibara in the popup window
4. You'll be redirected back with a successful connection

### MyAnimeList Integration

#### Getting API Credentials
1. Visit [MyAnimeList API Config](https://myanimelist.net/apiconfig)
2. Create a new application
3. Set redirect URI to: `http://your-domain:3000/integrations/mal/callback`
4. Copy the Client ID and Client Secret

#### Connection Process
1. Enter your Client ID and Client Secret (or use environment variables)
2. Click "Connect MyAnimeList"
3. Authorize Kuroibara in the popup window
4. Complete the OAuth flow to establish connection

### Kitsu Integration

#### Simple Authentication
Kitsu uses direct username/password authentication - no API credentials needed!

#### Connection Process
1. Enter your Kitsu username and password
2. Click "Connect Kitsu"
3. Your account will be connected immediately

## ⚙️ Sync Settings

Each integration offers granular control over what data to synchronize:

### Available Sync Options
- **Auto-sync on changes**: Automatically sync when you update manga in Kuroibara
- **Sync reading progress**: Keep chapter progress in sync
- **Sync ratings**: Synchronize your manga ratings
- **Sync status**: Keep reading status (reading, completed, plan to read, etc.) in sync

### Manual Sync
You can trigger manual synchronization at any time using the "Sync Now" button for each connected service.

## 📊 Status Mapping

Kuroibara automatically maps reading statuses between different services:

| Kuroibara Status | Anilist | MyAnimeList | Kitsu |
|------------------|---------|-------------|-------|
| Reading | CURRENT | reading | current |
| Completed | COMPLETED | completed | completed |
| Plan to Read | PLANNING | plan_to_read | planned |
| On Hold | PAUSED | on_hold | on_hold |
| Dropped | DROPPED | dropped | dropped |

## 🔄 Sync Behavior

### Bidirectional Sync
- Changes made in Kuroibara are pushed to connected services
- Changes made on external services are pulled into Kuroibara
- Conflicts are resolved using the most recent timestamp

### Rating Conversion
- **Anilist**: 10-point scale (1-10)
- **MyAnimeList**: 10-point scale (1-10)
- **Kitsu**: 20-point scale (automatically converted)

### Progress Tracking
- Chapter progress is synchronized across all platforms
- Volume information is preserved when available
- Reading dates (start/finish) are maintained

## 🛠️ Troubleshooting

### Common Issues

#### "Failed to connect" errors
- Verify your API credentials are correct
- Check that redirect URIs match exactly
- Ensure your application is approved (for MAL)

#### Sync not working
- Check that sync is enabled in settings
- Verify the service connection is still active
- Try disconnecting and reconnecting the service

#### Missing manga
- Not all manga may be available on all services
- Kuroibara will skip items that can't be found
- Check the sync logs for detailed information

### Getting Help
- Check the connection status indicators
- Review sync logs in the integration settings
- Disconnect and reconnect if issues persist

## 🔒 Privacy & Security

### Data Handling
- API credentials are stored securely in the database
- Access tokens are encrypted
- No passwords are stored (except for Kitsu, which uses secure OAuth2)

### Permissions
- Kuroibara only requests necessary permissions
- You can revoke access at any time through the service's settings
- Data sync can be disabled without disconnecting

### What's Synced
- Reading progress and status
- Ratings and reviews (if enabled)
- Manga list additions/removals
- Reading dates and notes

### What's NOT Synced
- Personal information
- Private messages or social features
- Payment or subscription information
- Other users' data

## 📈 Advanced Features

### Multiple Account Support
- Connect multiple services simultaneously
- Each service operates independently
- Conflicts between services are handled gracefully

### Selective Sync
- Choose which data types to sync per service
- Disable auto-sync for manual control
- Pause syncing temporarily without disconnecting

### Sync Monitoring
- Real-time sync status indicators
- Last sync timestamps
- Error reporting and retry mechanisms

## 🆘 Support

If you encounter issues with external integrations:

1. Check the service's official documentation
2. Verify your API credentials and permissions
3. Review Kuroibara's integration logs
4. Report issues on the GitHub repository

## 🔧 Technical Implementation

### Architecture Overview
- **Backend**: FastAPI with async SQLAlchemy ORM
- **Database**: PostgreSQL with dedicated integration tables
- **Frontend**: Vue.js 3 with Pinia state management
- **Authentication**: OAuth2 flows with secure token storage

### Database Schema
```sql
-- External integrations table
CREATE TABLE external_integrations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    integration_type VARCHAR(50) NOT NULL,
    client_id VARCHAR(255),
    client_secret VARCHAR(255),
    access_token TEXT,
    refresh_token TEXT,
    external_user_id VARCHAR(255),
    external_username VARCHAR(255),
    sync_enabled BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMP,
    last_sync_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Manga mapping table
CREATE TABLE external_manga_mappings (
    id UUID PRIMARY KEY,
    integration_id UUID REFERENCES external_integrations(id),
    manga_id UUID REFERENCES manga(id),
    external_manga_id VARCHAR(255) NOT NULL,
    external_title VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints
- `GET /api/v1/integrations/settings` - Get integration status
- `POST /api/v1/integrations/setup` - Setup integration credentials
- `POST /api/v1/integrations/anilist/connect` - Connect Anilist account
- `POST /api/v1/integrations/myanimelist/connect` - Connect MAL account
- `POST /api/v1/integrations/kitsu/connect` - Connect Kitsu account
- `PUT /api/v1/integrations/{type}` - Update integration settings
- `DELETE /api/v1/integrations/{type}` - Disconnect integration
- `POST /api/v1/integrations/sync` - Trigger manual sync

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/kuroibara

# Optional: Pre-configure API credentials
ANILIST_CLIENT_ID=your_anilist_client_id
ANILIST_CLIENT_SECRET=your_anilist_client_secret
MAL_CLIENT_ID=your_mal_client_id
MAL_CLIENT_SECRET=your_mal_client_secret

# Frontend (optional)
VITE_ANILIST_CLIENT_ID=your_anilist_client_id
VITE_MAL_CLIENT_ID=your_mal_client_id
```

---

*This guide covers the basic setup and usage of external integrations. For technical implementation details, see the developer documentation.*
