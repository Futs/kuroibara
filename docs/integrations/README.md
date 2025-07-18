# External Integrations Documentation

This directory contains comprehensive documentation for Kuroibara's external integration system, which allows seamless synchronization with popular manga tracking services.

## 📚 Documentation Files

### User Guides
- **[External Integrations Guide](EXTERNAL_INTEGRATIONS_GUIDE.md)** - Complete user guide for setting up and using integrations with Anilist, MyAnimeList, and Kitsu

### Technical Documentation
- **[Integration Technical Guide](INTEGRATION_TECHNICAL_GUIDE.md)** - Developer documentation covering implementation details, API endpoints, and architecture

### Development Reports
- **[Kitsu Integration Summary](KITSU_INTEGRATION_SUMMARY.md)** - Summary of Kitsu integration implementation and settings reorganization
- **[Integration Validation Report](INTEGRATION_VALIDATION_REPORT.md)** - Comprehensive validation results for the integration system

## 🔗 Supported Services

| Service | Authentication | Features | Status |
|---------|---------------|----------|--------|
| **Anilist** | OAuth2 Authorization Code | Reading progress, ratings, status tracking | ✅ Complete |
| **MyAnimeList** | OAuth2 with PKCE | Reading progress, ratings, status tracking | ✅ Complete |
| **Kitsu** | Username/Password | Reading progress, ratings (20-point), status tracking | ✅ Complete |

## 🚀 Quick Start

1. **For Users**: Start with the [External Integrations Guide](EXTERNAL_INTEGRATIONS_GUIDE.md)
2. **For Developers**: Review the [Integration Technical Guide](INTEGRATION_TECHNICAL_GUIDE.md)
3. **For Contributors**: Check the validation reports for implementation details

## 🎯 Key Features

### Seamless Synchronization
- **Bidirectional Sync**: Changes sync both ways between Kuroibara and external services
- **Real-time Updates**: Auto-sync on changes with manual sync options
- **Conflict Resolution**: Smart handling of conflicting data using timestamps

### Flexible Authentication
- **Multiple OAuth Flows**: Support for different OAuth2 implementations
- **Environment Variables**: Optional pre-configuration of API credentials
- **UI Configuration**: Easy setup through the web interface

### Comprehensive Data Sync
- **Reading Progress**: Chapter and volume progress tracking
- **Ratings**: Support for different rating scales with automatic conversion
- **Status Tracking**: Complete reading status synchronization
- **Metadata**: Sync reading dates, notes, and other metadata

### User-Friendly Interface
- **Dedicated Settings Tab**: Organized integration management
- **Visual Status Indicators**: Clear connection and sync status
- **Granular Controls**: Fine-tuned sync settings per service
- **Error Handling**: Comprehensive error reporting and recovery

## 🔧 Technical Highlights

### Architecture
- **Modular Design**: Service-specific clients with common interfaces
- **Async Operations**: Non-blocking sync operations
- **Database Integration**: Secure credential storage and manga mapping
- **Frontend State Management**: Reactive UI with Pinia store

### Security
- **Encrypted Storage**: Secure token and credential storage
- **OAuth2 Compliance**: Industry-standard authentication flows
- **Permission Scoping**: Minimal required permissions
- **Token Management**: Automatic refresh and expiration handling

### Performance
- **Rate Limiting**: Respect for external service limits
- **Batch Operations**: Efficient bulk synchronization
- **Caching**: Smart caching to reduce API calls
- **Error Recovery**: Robust retry mechanisms

## 📖 Usage Examples

### Setting Up Anilist Integration
```bash
# Option 1: Environment variables
ANILIST_CLIENT_ID=your_client_id
ANILIST_CLIENT_SECRET=your_client_secret

# Option 2: UI configuration
# Navigate to Settings > Integrations > Anilist
# Enter credentials and click "Connect Anilist"
```

### Triggering Manual Sync
```javascript
// Frontend store action
await integrationsStore.triggerSync('anilist');

// API endpoint
POST /api/v1/integrations/sync
{
  "integration_type": "anilist",
  "force_full_sync": false
}
```

### Checking Integration Status
```javascript
// Frontend store getter
const isConnected = integrationsStore.isAnilistConnected;

// API endpoint
GET /api/v1/integrations/settings
```

## 🛠️ Development

### Adding New Integrations
1. Implement the `BaseIntegrationClient` interface
2. Add the new integration type to the enum
3. Create authentication schemas and API endpoints
4. Update the frontend store and UI components
5. Add comprehensive tests

### Testing
```bash
# Run integration tests
docker compose exec backend python test_integration_validation.py

# Run specific service tests
docker compose exec backend python -m pytest tests/test_integrations.py
```

### Database Migrations
```bash
# Create migration for integration changes
docker compose exec backend alembic revision --autogenerate -m "integration_update"

# Apply migrations
docker compose exec backend alembic upgrade head
```

## 📊 Monitoring

### Sync Status Monitoring
- Real-time sync status in the UI
- Last sync timestamps and results
- Error logging and reporting
- Performance metrics tracking

### Health Checks
- Integration connection status
- Token expiration monitoring
- API rate limit tracking
- Service availability checks

## 🆘 Support

### Common Issues
- **Connection Problems**: Check API credentials and service status
- **Sync Failures**: Review error logs and retry mechanisms
- **Missing Data**: Verify service availability and permissions
- **Performance Issues**: Check rate limits and network connectivity

### Getting Help
1. Review the troubleshooting sections in the user guide
2. Check the technical documentation for implementation details
3. Examine the validation reports for known issues
4. Report bugs on the GitHub repository

---

*This documentation is maintained alongside the codebase. For the latest updates, check the repository's main branch.*
