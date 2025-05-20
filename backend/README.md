# Kurobara Backend

The backend API for the Kurobara manga/manhua/manhwa library application.

## Features

- User authentication with 2FA
- Manga search across 100+ providers with a flexible provider system
  - Built-in support for MangaDex, MangaPlus, MangaSee
  - Configurable providers for ArcaneScans, RadiantScans, ReaperScans, VizShonenJump, and many more
  - Easy to add new providers through configuration files
- Library management with categories and reading lists
- Reading progress tracking and bookmarking
- Background task management for downloads
- File import functionality (CBZ, CBR, 7Z)
- Directory import for chapters
- Comprehensive API for frontend integration

## Tech Stack

- Python 3.12
- FastAPI with background tasks
- PostgreSQL 16
- Valkey (Redis fork) for caching
- SQLAlchemy ORM with async support
- Alembic for migrations
- Pytest for testing

## Development

### Prerequisites

- Docker and Docker Compose
- Python 3.12

### Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and configure the environment variables
3. Run `docker-compose up -d` to start the development environment

### Database Migrations

To create a new migration:

```bash
docker-compose exec backend alembic revision --autogenerate -m "Migration message"
```

To run migrations:

```bash
docker-compose exec backend alembic upgrade head
```

### API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Testing

To run tests:

```bash
docker-compose exec backend pytest
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
