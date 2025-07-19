# Kuroibara Backend

The backend API for the Kuroibara manga/manhua/manhwa library application.

## Features

- User authentication with 2FA support
- Manga search across 80+ providers with a flexible provider system
  - Built-in support for MangaDex, MangaPlus, TCBScans, and many more
  - Template-based provider system for community contributions
  - Easy to add new providers through GitHub issue templates (no coding required)
- Smart library management with categories and reading lists
- Advanced reading progress tracking and bookmarking
- Background task management for downloads and maintenance
- File import functionality (CBZ, CBR, 7Z formats)
- Directory import for chapters and bulk operations
- Comprehensive REST API with OpenAPI documentation
- Optional FlareSolverr integration for Cloudflare bypass
- Reading analytics and achievement system

## Tech Stack

- Python 3.13
- FastAPI 0.115+ with background tasks
- PostgreSQL 16
- Redis for caching and session storage
- SQLAlchemy ORM with async support
- Alembic for database migrations
- Pytest for comprehensive testing

## Development

### Prerequisites

- Docker and Docker Compose
- Python 3.13 (for local development)

### Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and configure the environment variables
3. Run `docker compose up -d` to start the development environment

### Quick Start with Docker Hub

```bash
# Pull and run with Docker Compose
curl -O https://raw.githubusercontent.com/Futs/kuroibara/main/docker-compose.yml
docker compose up -d
```

### Database Migrations

To create a new migration:

```bash
docker compose exec backend alembic revision --autogenerate -m "Migration message"
```

To run migrations:

```bash
docker compose exec backend alembic upgrade head
```

### API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

To run tests:

```bash
docker compose exec backend pytest
```

To run tests with coverage:

```bash
docker compose exec backend pytest --cov=app --cov-report=html
```

## Project Structure

```
backend/
├── alembic/                  # Database migrations
├── app/                      # Application code
│   ├── api/                  # API endpoints
│   │   └── api_v1/           # API v1 endpoints
│   ├── core/                 # Core application code
│   │   ├── providers/        # Manga providers
│   │   │   ├── config/       # Provider configurations
│   │   │   └── ...           # Provider implementations
│   │   └── services/         # Application services
│   ├── db/                   # Database related code
│   ├── models/               # Database models
│   └── schemas/              # Pydantic schemas
├── scripts/                  # Utility scripts
├── tests/                    # Tests
└── Dockerfile                # Docker configuration
```
