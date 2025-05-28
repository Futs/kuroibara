# Provider Monitoring and Favorites Enhancement

This document provides implementation details for the two major enhancements added to the Kurobara manga application:

1. **Provider Health Monitoring System**
2. **User Favorites Management**

## 🚀 Quick Start

### 1. Database Migration
```bash
cd backend
alembic upgrade head
```

### 2. Start the Application
The provider monitoring system will automatically:
- Test all providers on startup
- Begin continuous health monitoring
- Initialize provider status records

## 📊 Provider Health Monitoring

### Overview
The provider monitoring system continuously tracks the health and availability of all manga providers, providing real-time status information and automatically disabling unhealthy providers in the UI.

### Key Features
- **Startup Testing**: All providers tested when application starts
- **Continuous Monitoring**: Background service monitors provider health
- **Configurable Intervals**: Users can set check intervals (30min to monthly)
- **Status Tracking**: Comprehensive health metrics and statistics
- **UI Integration**: Unhealthy providers are grayed out
- **Admin Controls**: Superusers can manage provider settings

### API Endpoints

#### Get Providers with Status
```http
GET /api/v1/providers/
```
Returns enhanced provider information including health status.

#### Get Detailed Provider Status
```http
GET /api/v1/providers/status
```
Returns comprehensive status information for all providers.

#### Update Provider Settings (Admin Only)
```http
PATCH /api/v1/providers/{provider_id}/status
Content-Type: application/json

{
  "is_enabled": true,
  "check_interval": 60,
  "max_consecutive_failures": 3
}
```

#### Test Provider Manually
```http
POST /api/v1/providers/{provider_id}/test
```
Manually trigger a health check for a specific provider.

#### Update User Check Interval
```http
PATCH /api/v1/providers/check-interval
Content-Type: application/json

{
  "interval": 60
}
```

### Provider Status Model
```python
class ProviderStatus:
    provider_id: str              # Unique provider identifier
    provider_name: str            # Display name
    provider_url: str             # Provider URL
    status: str                   # ACTIVE, DOWN, UNKNOWN, TESTING
    last_check: datetime          # Last health check time
    response_time: int            # Response time in milliseconds
    consecutive_failures: int     # Number of consecutive failures
    total_checks: int             # Total health checks performed
    successful_checks: int        # Number of successful checks
    uptime_percentage: int        # Uptime percentage (0-100)
    is_enabled: bool              # Whether monitoring is enabled
    check_interval: int           # Check interval in minutes
    max_consecutive_failures: int # Failure threshold
```

### Check Intervals
- **30 minutes**: Frequent monitoring
- **60 minutes**: Default interval
- **120 minutes**: Less frequent monitoring
- **Daily (1440 minutes)**: Once per day
- **Weekly (10080 minutes)**: Once per week
- **Monthly (43200 minutes)**: Once per month

## ⭐ User Favorites System

### Overview
The favorites system allows users to mark manga as favorites, creating a personalized collection that's easily accessible and manageable.

### Key Features
- **Add/Remove Favorites**: Simple favorite management
- **Bulk Operations**: Update multiple manga at once
- **Status Checking**: Check if manga is favorited
- **Count Tracking**: Get total favorites count
- **Pagination**: Paginated favorites list
- **Library Integration**: Uses existing database structure

### API Endpoints

#### Get User Favorites
```http
GET /api/v1/favorites/?page=1&limit=20
```
Returns paginated list of user's favorite manga.

#### Add to Favorites
```http
POST /api/v1/favorites/{manga_id}
```
Adds a manga to user's favorites list.

#### Remove from Favorites
```http
DELETE /api/v1/favorites/{manga_id}
```
Removes a manga from user's favorites list.

#### Check Favorite Status
```http
GET /api/v1/favorites/{manga_id}/status
```
Returns whether a manga is in user's favorites.

#### Get Favorites Count
```http
GET /api/v1/favorites/count
```
Returns the total number of favorited manga.

#### Bulk Update Favorites
```http
PATCH /api/v1/favorites/bulk
Content-Type: application/json

{
  "manga_ids": ["uuid1", "uuid2", "uuid3"],
  "is_favorite": true
}
```

### Response Examples

#### Favorites List Response
```json
[
  {
    "id": "uuid",
    "user_id": "user_uuid",
    "manga_id": "manga_uuid",
    "is_favorite": true,
    "custom_title": null,
    "rating": 4.5,
    "notes": "Great series!",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "manga": {
      "id": "manga_uuid",
      "title": "Manga Title",
      "description": "Manga description...",
      "cover_image": "https://example.com/cover.jpg"
    }
  }
]
```

#### Favorite Status Response
```json
{
  "manga_id": "manga_uuid",
  "is_favorite": true
}
```

## 🔧 Technical Implementation

### Database Schema Changes

#### New Table: provider_status
```sql
CREATE TABLE provider_status (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    provider_id VARCHAR(100) UNIQUE NOT NULL,
    provider_name VARCHAR(100) NOT NULL,
    provider_url VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'unknown',
    last_check TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_time INTEGER,
    error_message TEXT,
    consecutive_failures INTEGER DEFAULT 0,
    total_checks INTEGER DEFAULT 0,
    successful_checks INTEGER DEFAULT 0,
    uptime_percentage INTEGER DEFAULT 100,
    is_enabled BOOLEAN DEFAULT TRUE,
    check_interval INTEGER DEFAULT 60,
    max_consecutive_failures INTEGER DEFAULT 3
);
```

#### Updated Table: users
```sql
ALTER TABLE users ADD COLUMN provider_check_interval INTEGER DEFAULT 60;
```

### Background Services

#### Provider Monitor Service
- Runs continuously in background
- Tests providers at scheduled intervals
- Updates database with health status
- Handles concurrent testing with semaphores
- Graceful error handling and recovery

#### Service Lifecycle
```python
# Startup
await provider_monitor.test_all_providers_on_startup()
await provider_monitor.start_monitoring()

# Shutdown
await provider_monitor.stop_monitoring()
```

### Health Check Implementation
Each provider implements a health check method:

```python
async def health_check(self, timeout: int = 30) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Returns:
        - bool: Whether provider is healthy
        - Optional[int]: Response time in milliseconds
        - Optional[str]: Error message if unhealthy
    """
```

## 🎨 Frontend Integration

### Provider Status Display
- **Green**: Healthy providers (status: ACTIVE)
- **Red**: Unhealthy providers (status: DOWN)
- **Gray**: Unknown status or disabled providers
- **Yellow**: Currently being tested (status: TESTING)

### Favorites UI Elements
- **Star Icon**: Toggle favorite status
- **Favorites Page**: Dedicated favorites management
- **Bulk Actions**: Select multiple manga for bulk operations
- **Filter Options**: Filter by favorite status

## 🔒 Security & Permissions

### Provider Management
- **Regular Users**: Can view provider status, update personal check interval
- **Superusers**: Can modify provider settings, enable/disable providers

### Favorites Management
- **User Isolation**: Users can only manage their own favorites
- **Data Validation**: All inputs validated and sanitized

## 📈 Monitoring & Analytics

### Health Metrics Tracked
- Response times
- Uptime percentages
- Failure counts
- Success rates
- Historical data

### Logging
- Provider health check results
- User favorite actions
- System errors and warnings
- Performance metrics

## 🚨 Error Handling

### Provider Monitoring
- Graceful degradation when providers are down
- Automatic retry mechanisms
- Fallback to cached data when possible
- Non-blocking startup if monitoring fails

### Favorites System
- Validation of manga existence
- Duplicate prevention
- Transaction rollback on errors
- Comprehensive error messages

## 🔧 Configuration

### Environment Variables
No new environment variables required. Uses existing database and Redis configuration.

### Default Settings
- Provider check interval: 60 minutes
- Max consecutive failures: 3
- Health check timeout: 30 seconds
- Concurrent check limit: 5 providers

## 📝 Testing

### Test Script
Run the comprehensive test script:
```bash
cd backend
python test_enhancements.py
```

### Manual Testing
1. Check provider status: `GET /api/v1/providers/`
2. Add manga to favorites: `POST /api/v1/favorites/{manga_id}`
3. View favorites: `GET /api/v1/favorites/`
4. Test provider manually: `POST /api/v1/providers/{provider_id}/test`

This implementation provides a robust foundation for provider monitoring and user favorites while maintaining backward compatibility and following existing codebase patterns.
