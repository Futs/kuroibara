# System Health Endpoints

## Overview

The Kuroibara system provides comprehensive health monitoring endpoints for system administrators, monitoring tools, and load balancers. These endpoints are **public** (no authentication required) to ensure they can be accessed by external monitoring systems.

## Available Endpoints

### 1. System Health - `/api/v1/health/`

**Purpose**: Comprehensive system health check including all components  
**Method**: `GET`  
**Authentication**: None required  
**Response Time**: ~2-3 seconds (includes indexer connectivity tests)

**Response Format**:
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": 1756046050.9374444,
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 1.44,
      "message": "Database connection successful"
    },
    "indexers": {
      "status": "healthy",
      "response_time_ms": 2773.95,
      "healthy_count": 3,
      "total_count": 3,
      "details": {
        "mangaupdates": {
          "status": "healthy",
          "tier": "primary",
          "message": "Connected to MangaUpdates API"
        },
        "madaradex": {
          "status": "healthy",
          "tier": "secondary",
          "message": "Connected to MadaraDex"
        },
        "mangadex": {
          "status": "healthy",
          "tier": "tertiary",
          "message": "Connected to MangaDex API"
        }
      },
      "message": "3/3 indexers healthy"
    },
    "providers": {
      "status": "healthy",
      "response_time_ms": 0.01,
      "enabled_count": 12,
      "total_count": 12,
      "message": "12/12 providers enabled"
    }
  },
  "summary": {
    "healthy_components": 3,
    "total_components": 3,
    "health_percentage": 100.0,
    "total_response_time_ms": 2776.43
  }
}
```

### 2. Quick Health - `/api/v1/health/quick`

**Purpose**: Fast health check for load balancers and basic monitoring  
**Method**: `GET`  
**Authentication**: None required  
**Response Time**: <10ms (minimal checks)

**Response Format**:
```json
{
  "status": "healthy|unhealthy",
  "timestamp": 1756046044.81925,
  "message": "Service is running"
}
```

### 3. Indexers Health - `/api/v1/health/indexers`

**Purpose**: Detailed health check for indexer services only  
**Method**: `GET`  
**Authentication**: None required  
**Response Time**: ~2-3 seconds (indexer connectivity tests)

**Response Format**:
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": 1756046050.9374444,
  "response_time_ms": 2773.95,
  "summary": {
    "healthy_count": 3,
    "total_count": 3,
    "health_percentage": 100.0
  },
  "indexers": {
    "mangaupdates": {
      "status": "healthy",
      "tier": "primary",
      "message": "Connected to MangaUpdates API"
    },
    "madaradex": {
      "status": "healthy",
      "tier": "secondary",
      "message": "Connected to MadaraDex"
    },
    "mangadex": {
      "status": "healthy",
      "tier": "tertiary",
      "message": "Connected to MangaDex API"
    }
  }
}
```

## Health Status Definitions

### Overall Status
- **`healthy`**: All components are functioning normally
- **`degraded`**: Some components have issues but core functionality works
- **`unhealthy`**: Critical components are failing

### Component Status
- **`healthy`**: Component is functioning normally
- **`degraded`**: Component has issues but is partially functional
- **`unhealthy`**: Component is not functioning

## Health Check Logic

### System Health (`/api/v1/health/`)
1. **Database**: Tests connection with `SELECT 1`
2. **Indexers**: Tests connectivity to all 3 indexers (MangaUpdates, MadaraDex, MangaDex)
3. **Providers**: Checks provider registry and database status

**Overall Status Logic**:
- `healthy`: All components healthy
- `degraded`: At least one component healthy
- `unhealthy`: No components healthy

### Indexers Health Logic
- `healthy`: Primary indexer (MangaUpdates) is working
- `degraded`: Primary indexer down but secondary/tertiary working
- `unhealthy`: All indexers down

## Monitoring Integration

### Load Balancer Health Checks
Use the quick health endpoint for fast health checks:
```bash
curl -f http://localhost:8000/api/v1/health/quick
```

### Monitoring Systems (Prometheus, etc.)
Use the system health endpoint for comprehensive monitoring:
```bash
curl http://localhost:8000/api/v1/health/
```

### Alerting Thresholds
- **Critical**: `status: "unhealthy"`
- **Warning**: `status: "degraded"`
- **Info**: `health_percentage < 100`

## Example Usage

### Basic Health Check
```bash
curl http://localhost:8000/api/v1/health/quick
```

### Comprehensive Health Check
```bash
curl http://localhost:8000/api/v1/health/ | jq '.summary'
```

### Indexer-Specific Monitoring
```bash
curl http://localhost:8000/api/v1/health/indexers | jq '.indexers'
```

### Health Check Script
```bash
#!/bin/bash
HEALTH_URL="http://localhost:8000/api/v1/health/"
STATUS=$(curl -s $HEALTH_URL | jq -r '.status')

if [ "$STATUS" = "healthy" ]; then
    echo "✅ System is healthy"
    exit 0
elif [ "$STATUS" = "degraded" ]; then
    echo "⚠️ System is degraded"
    exit 1
else
    echo "❌ System is unhealthy"
    exit 2
fi
```

## Performance Characteristics

### Response Times
- **Quick Health**: <10ms (no external calls)
- **System Health**: 2-3 seconds (includes indexer tests)
- **Indexers Health**: 2-3 seconds (indexer connectivity only)

### Resource Usage
- **CPU**: Minimal impact
- **Memory**: <1MB per request
- **Network**: Tests external indexer APIs

### Caching
- No caching implemented (real-time health status)
- Consider implementing short-term caching (30-60 seconds) for high-frequency monitoring

## Troubleshooting

### Common Issues
1. **Slow Response Times**: Indexer connectivity issues
2. **Database Unhealthy**: PostgreSQL connection problems
3. **Indexers Degraded**: External API rate limiting or downtime
4. **Providers Issues**: Database query problems

### Debug Information
All endpoints include detailed error messages and response times to help diagnose issues.

## Security Considerations

- **Public Access**: Health endpoints are intentionally public
- **Information Disclosure**: Minimal sensitive information exposed
- **Rate Limiting**: Consider implementing rate limiting for abuse prevention
- **Monitoring**: Log health check requests for security monitoring
