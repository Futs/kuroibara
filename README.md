# Kurobara (Black Rose)

A modern web application for manga, manhua, and manhwa enthusiasts.

## Features

- Search for manga/manhua/manhwa from 100+ online providers including:
  - MangaDex, MangaPlus, MangaSee
  - ArcaneScans, RadiantScans, ReaperScans
  - VizShonenJump, TCBScans, OmegaScans
  - And many more (see full list in the documentation)
- Add manga/manhua/manhwa with cover and metadata to your library
- Download manga/manhua/manhwa to your library with background processing
- Read manga/manhua/manhwa directly in the app
- Import CBZ, CBR, or 7Z files to your library
- Import directories of images as chapters
- User-defined and pre-made categories
- Customizable dashboard with pinned categories
- NSFW/Explicit content management with blur option
- User registration with 2FA
- Reading progress tracking and bookmarking
- Custom reading lists
- Background task management for downloads

## Tech Stack

### Backend
- Python 3.12
- FastAPI with background tasks
- PostgreSQL 16
- Valkey (Redis fork) for caching
- SQLAlchemy ORM with async support
- Alembic for migrations
- Pytest for testing

### Frontend
- Vue.js
- Tailwind CSS

## Development

### Prerequisites
- Docker and Docker Compose
- Python 3.12
- Node.js 18+ and npm

### Setup
1. Clone the repository
2. Copy `.env.example` to `.env` and configure the environment variables
3. Run `docker-compose up -d` to start the production environment

### Development Mode
For development with hot-reloading:

```bash
# Start the development environment
docker-compose -f docker-compose.dev.yml up -d

# Access the frontend at http://localhost:3000
# Access the backend API at http://localhost:8000
# Access the API documentation at http://localhost:8000/api/docs
```

### Frontend Development
You can also run the frontend separately:

```bash
# Navigate to the frontend app directory
cd frontend/app

# Install dependencies
npm install

# Start the development server
npm run dev

# Build for production
npm run build
```

## License

[MIT License](LICENSE)
