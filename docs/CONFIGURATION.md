# Configuration Guide

## Environment Variables

### Database Configuration
```bash
# PostgreSQL Database Settings
DB_HOST=postgres                    # Database host (default: postgres for Docker)
DB_PORT=5432                       # Database port (default: 5432)
DB_USERNAME=kuroibara              # Database username
DB_PASSWORD=your_secure_password   # Database password (change this!)
DB_DATABASE=kuroibara              # Database name
```

### Cache Configuration
```bash
# Valkey/Redis Cache Settings
VALKEY_HOST=valkey                 # Cache host (default: valkey for Docker)
VALKEY_PORT=6379                   # Cache port (default: 6379)
VALKEY_PASSWORD=                   # Cache password (optional)
VALKEY_DB=0                        # Cache database number (default: 0)
```

### Security Configuration
```bash
# Security Settings
SECRET_KEY=your_very_long_secret_key_here  # JWT signing key (generate a strong one!)
ACCESS_TOKEN_EXPIRE_MINUTES=30             # JWT token expiration (default: 30 minutes)
REFRESH_TOKEN_EXPIRE_DAYS=7                # Refresh token expiration (default: 7 days)
ALGORITHM=HS256                            # JWT algorithm (default: HS256)

# Password Requirements
MIN_PASSWORD_LENGTH=8                      # Minimum password length
REQUIRE_UPPERCASE=true                     # Require uppercase letters
REQUIRE_LOWERCASE=true                     # Require lowercase letters
REQUIRE_NUMBERS=true                       # Require numbers
REQUIRE_SPECIAL_CHARS=false                # Require special characters
```

### Provider Monitoring
```bash
# Provider Health Check Settings
PROVIDER_CHECK_INTERVAL=60                 # Check interval in minutes (default: 60)
MAX_CONCURRENT_CHECKS=5                    # Maximum concurrent health checks
PROVIDER_TIMEOUT=30                        # Request timeout in seconds
RETRY_ATTEMPTS=3                           # Number of retry attempts
RETRY_DELAY=5                              # Delay between retries in seconds

# Provider Status Thresholds
UNHEALTHY_THRESHOLD=3                      # Consecutive failures before marking unhealthy
HEALTHY_THRESHOLD=2                        # Consecutive successes before marking healthy
```

### Email Configuration
```bash
# SMTP Settings (for production)
SMTP_HOST=smtp.gmail.com                   # SMTP server host
SMTP_PORT=587                              # SMTP server port
SMTP_USERNAME=your_email@gmail.com         # SMTP username
SMTP_PASSWORD=your_app_password            # SMTP password or app password
SMTP_TLS=true                              # Use TLS encryption
SMTP_SSL=false                             # Use SSL encryption

# Email Settings
FROM_EMAIL=noreply@kuroibara.com           # Default sender email
FROM_NAME=Kuroibara                        # Default sender name
```

### Application Settings
```bash
# General Application Settings
APP_NAME=Kuroibara                         # Application name
APP_VERSION=0.1.0                          # Application version
DEBUG=false                                # Debug mode (set to false in production)
ENVIRONMENT=production                     # Environment (development/staging/production)

# API Settings
API_V1_PREFIX=/api/v1                      # API version prefix
DOCS_URL=/api/docs                         # Swagger UI URL
REDOC_URL=/api/redoc                       # ReDoc URL
OPENAPI_URL=/api/openapi.json              # OpenAPI JSON URL

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com  # Allowed origins
ALLOWED_METHODS=GET,POST,PUT,DELETE,PATCH  # Allowed HTTP methods
ALLOWED_HEADERS=*                          # Allowed headers
```

### File Storage Configuration
```bash
# File Storage Settings
UPLOAD_DIR=/app/uploads                    # Upload directory
MAX_FILE_SIZE=100MB                        # Maximum file size
ALLOWED_EXTENSIONS=cbz,cbr,7z,zip,rar      # Allowed file extensions

# Image Processing
MAX_IMAGE_WIDTH=2048                       # Maximum image width for processing
MAX_IMAGE_HEIGHT=2048                      # Maximum image height for processing
IMAGE_QUALITY=85                           # JPEG compression quality (1-100)
```

### Background Tasks
```bash
# Task Queue Settings
TASK_QUEUE_URL=redis://valkey:6379/1       # Task queue Redis URL
MAX_WORKERS=4                              # Maximum number of worker processes
TASK_TIMEOUT=300                           # Task timeout in seconds
RESULT_EXPIRES=3600                        # Task result expiration in seconds
```

## Docker Configuration

### Production Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=postgres
      - VALKEY_HOST=valkey
    depends_on:
      - postgres
      - valkey
    volumes:
      - ./uploads:/app/uploads

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - app

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: kuroibara
      POSTGRES_USER: kuroibara
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  valkey:
    image: valkey/valkey:7
    volumes:
      - valkey_data:/data

volumes:
  postgres_data:
  valkey_data:
```

### Development Docker Compose
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - DEBUG=true
      - ENVIRONMENT=development
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads
    depends_on:
      - postgres
      - valkey
      - mailhog

  mailhog:
    image: mailhog/mailhog
    ports:
      - "8025:8025"
      - "1025:1025"
```

## Database Configuration

### PostgreSQL Settings
```sql
-- Recommended PostgreSQL settings for production
-- postgresql.conf

# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Connection settings
max_connections = 100
listen_addresses = '*'

# Performance settings
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging settings
log_statement = 'all'
log_duration = on
log_min_duration_statement = 1000
```

### Database Initialization
```bash
# Initialize database with required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";
```

## Nginx Configuration

### Production Nginx Config
```nginx
# /etc/nginx/sites-available/kuroibara
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # File uploads
    client_max_body_size 100M;
}
```

## Security Configuration

### SSL/TLS Setup
```bash
# Generate SSL certificate with Let's Encrypt
certbot --nginx -d yourdomain.com

# Or use custom certificates
ssl_certificate /path/to/certificate.crt;
ssl_certificate_key /path/to/private.key;
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
```

### Firewall Configuration
```bash
# UFW firewall rules
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

## Monitoring Configuration

### Health Check Endpoints
```bash
# Application health checks
GET /api/v1/health              # Application health
GET /api/v1/health/database     # Database connectivity
GET /api/v1/health/cache        # Cache connectivity
GET /api/v1/providers/status    # Provider health status
```

### Logging Configuration
```python
# logging.conf
[loggers]
keys=root,kuroibara

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler

[logger_kuroibara]
level=DEBUG
handlers=consoleHandler,fileHandler
qualname=kuroibara
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=DEBUG
formatter=simpleFormatter
args=('/app/logs/kuroibara.log',)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## Backup Configuration

### Database Backup
```bash
# Automated database backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h postgres -U kuroibara kuroibara > "$BACKUP_DIR/kuroibara_$DATE.sql"

# Keep only last 7 days of backups
find $BACKUP_DIR -name "kuroibara_*.sql" -mtime +7 -delete
```

### File Backup
```bash
# Backup uploaded files
rsync -av /app/uploads/ /backups/uploads/
```
