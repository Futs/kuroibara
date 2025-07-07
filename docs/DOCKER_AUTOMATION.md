# Docker-Specific Automation Integration

## 🐳 Docker Integration with Automation Tools

### **1. Multi-stage Build with Version Info**

Update your Dockerfiles to include version information:

```dockerfile
# backend/Dockerfile
ARG VERSION=0.1.0
ARG BUILD_DATE
ARG GIT_SHA

# Build stage
FROM python:3.12-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim
WORKDIR /app

# Copy from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application
COPY . .

# Add version information
ARG VERSION
ARG BUILD_DATE
ARG GIT_SHA
ENV VERSION=$VERSION
ENV BUILD_DATE=$BUILD_DATE
ENV GIT_SHA=$GIT_SHA

# Labels for container metadata
LABEL version=$VERSION \
      build-date=$BUILD_DATE \
      git-sha=$GIT_SHA \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.revision=$GIT_SHA \
      org.opencontainers.image.title="Kuroibara Backend" \
      org.opencontainers.image.description="Manga platform backend API"

# Create version endpoint
RUN echo "from app import __version__; print(__version__)" > /app/version_check.py

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# frontend/Dockerfile
ARG VERSION=0.1.0
ARG BUILD_DATE
ARG GIT_SHA

# Build stage
FROM node:18-alpine as builder
WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source and build
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

# Add version information
ARG VERSION
ARG BUILD_DATE
ARG GIT_SHA
ENV VERSION=$VERSION
ENV BUILD_DATE=$BUILD_DATE
ENV GIT_SHA=$GIT_SHA

# Labels for container metadata
LABEL version=$VERSION \
      build-date=$BUILD_DATE \
      git-sha=$GIT_SHA \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.revision=$GIT_SHA \
      org.opencontainers.image.title="Kuroibara Frontend" \
      org.opencontainers.image.description="Manga platform frontend application"

# Create version info file
RUN echo "{\\"version\\": \\"$VERSION\\", \\"buildDate\\": \\"$BUILD_DATE\\", \\"gitSha\\": \\"$GIT_SHA\\"}" > /usr/share/nginx/html/version.json

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### **2. Docker Compose with Version Variables**

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      args:
        VERSION: ${VERSION:-0.1.0}
        BUILD_DATE: ${BUILD_DATE:-}
        GIT_SHA: ${GIT_SHA:-}
    environment:
      - VERSION=${VERSION:-0.1.0}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - valkey

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        VERSION: ${VERSION:-0.1.0}
        BUILD_DATE: ${BUILD_DATE:-}
        GIT_SHA: ${GIT_SHA:-}
    environment:
      - VERSION=${VERSION:-0.1.0}
    ports:
      - "3000:80"
    depends_on:
      - backend

  postgres:
    image: postgres:16
    environment:
      - POSTGRES_USER=${DB_USERNAME:-kuroibara}
      - POSTGRES_PASSWORD=${DB_PASSWORD:-password}
      - POSTGRES_DB=${DB_DATABASE:-kuroibara}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  valkey:
    image: valkey/valkey:7
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### **3. Version-aware Build Script**

```bash
#!/bin/bash
# build.sh - Enhanced build script with version info

set -e

# Get version information
VERSION=$(./version.sh current)
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GIT_SHA=$(git rev-parse --short HEAD)

echo "🔧 Building Kuroibara v$VERSION"
echo "📅 Build Date: $BUILD_DATE"
echo "🔗 Git SHA: $GIT_SHA"

# Export variables for docker-compose
export VERSION
export BUILD_DATE
export GIT_SHA

# Build with version information
docker-compose build --build-arg VERSION="$VERSION" --build-arg BUILD_DATE="$BUILD_DATE" --build-arg GIT_SHA="$GIT_SHA"

echo "✅ Build complete!"
echo "🏷️  Images tagged with version: $VERSION"
echo "📦 To run: docker-compose up -d"
```

### **4. Health Check Endpoints with Version**

Add version endpoints to your applications:

```python
# backend/app/api/api_v1/endpoints/health.py
from fastapi import APIRouter
from app import __version__
import os

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": __version__,
        "build_date": os.getenv("BUILD_DATE"),
        "git_sha": os.getenv("GIT_SHA"),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@router.get("/version")
async def get_version():
    return {
        "version": __version__,
        "build_date": os.getenv("BUILD_DATE"),
        "git_sha": os.getenv("GIT_SHA")
    }
```

```javascript
// frontend/src/api/health.js
export async function getVersion() {
  const response = await fetch('/version.json');
  return response.json();
}

// frontend/src/components/AppVersion.vue
<template>
  <div class="version-info">
    <span class="text-xs text-gray-500">
      v{{ version }} ({{ shortSha }})
    </span>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getVersion } from '../api/health'

const version = ref('0.1.0')
const shortSha = ref('')

onMounted(async () => {
  try {
    const versionInfo = await getVersion()
    version.value = versionInfo.version
    shortSha.value = versionInfo.gitSha
  } catch (error) {
    console.warn('Could not fetch version info:', error)
  }
})
</script>
```

### **5. Docker Registry Integration**

```bash
#!/bin/bash
# push.sh - Push versioned images to registry

set -e

VERSION=$(./version.sh current)
REGISTRY="ghcr.io/futs/kuroibara"

echo "📦 Pushing Kuroibara v$VERSION to registry..."

# Tag images
docker tag kuroibara-backend:latest "$REGISTRY-backend:$VERSION"
docker tag kuroibara-frontend:latest "$REGISTRY-frontend:$VERSION"

docker tag kuroibara-backend:latest "$REGISTRY-backend:latest"
docker tag kuroibara-frontend:latest "$REGISTRY-frontend:latest"

# Push versioned tags
docker push "$REGISTRY-backend:$VERSION"
docker push "$REGISTRY-frontend:$VERSION"

# Push latest tags
docker push "$REGISTRY-backend:latest"
docker push "$REGISTRY-frontend:latest"

echo "✅ Successfully pushed images:"
echo "🐳 $REGISTRY-backend:$VERSION"
echo "🐳 $REGISTRY-frontend:$VERSION"
```

### **6. Monitoring and Logging**

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./monitoring/loki:/etc/loki
    command: -config.file=/etc/loki/loki.yml

volumes:
  grafana_data:
```

### **7. Automated Testing in Docker**

```bash
#!/bin/bash
# test.sh - Run tests in Docker containers

set -e

echo "🧪 Running tests in Docker containers..."

# Backend tests
echo "🐍 Running backend tests..."
docker-compose -f docker-compose.test.yml run --rm backend-test

# Frontend tests
echo "🌐 Running frontend tests..."
docker-compose -f docker-compose.test.yml run --rm frontend-test

# Integration tests
echo "🔗 Running integration tests..."
docker-compose -f docker-compose.test.yml run --rm integration-test

echo "✅ All tests passed!"
```

### **8. Environment-specific Configurations**

```bash
# .env.production
VERSION=0.1.0
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# .env.staging
VERSION=0.1.0-dev
ENVIRONMENT=staging
LOG_LEVEL=DEBUG
DEBUG=true

# .env.development
VERSION=0.1.0-dev
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DEBUG=true
```

This integration ensures that your automation tools work seamlessly with your Docker-based infrastructure, providing version tracking, health monitoring, and automated builds! 🚀
