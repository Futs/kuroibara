[![Deploy](https://github.com/Futs/kuroibara/actions/workflows/deploy.yml/badge.svg)](https://github.com/Futs/kuroibara/actions/workflows/deploy.yml)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/Futs/kuroibara/releases)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Vue.js](https://img.shields.io/badge/vue.js-3.5-4FC08D.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-latest-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub Issues](https://img.shields.io/github/issues/Futs/kuroibara.svg)](https://github.com/Futs/kuroibara/issues)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


# Kuroibara (Black Rose) 🌹

A modern, full-featured web application for manga, manhua, and manhwa enthusiasts. Kuroibara provides a comprehensive platform for discovering, managing, and reading manga from multiple online sources.

> **⚠️ Development Status**: Kuroibara is currently in active development (v0.1.0). While the core features are functional, expect regular updates and potential breaking changes until v1.0.0 release.

## ✨ Features

### 📚 Content Management
- **Multi-Provider Search**: Access 100+ manga providers including MangaDex, MangaPlus, TCBScans, OmegaScans, and many more
- **Smart Library Management**: Add manga to your personal library with automatic metadata and cover art
- **Background Downloads**: Queue and download manga chapters with background processing
- **File Import Support**: Import CBZ, CBR, 7Z files and image directories as chapters
- **NSFW Content Control**: Blur NSFW content with user-configurable settings

### 👤 User Experience
- **User Profiles**: Customizable profiles with avatar support and external account linking (AniList, MyAnimeList)
- **Favorites System**: Star and manage your favorite manga with advanced search and filtering
- **Reading Progress**: Track your reading progress and bookmark chapters
- **Custom Categories**: Create and organize manga with user-defined categories
- **Responsive Design**: Modern Vue.js interface with Tailwind CSS styling

### 🔧 Advanced Features
- **Provider Health Monitoring**: Real-time monitoring of provider availability with automatic status updates
- **2FA Authentication**: Secure user registration and login with two-factor authentication
- **Session Management**: Configurable session persistence with "Remember Me" functionality
- **Background Tasks**: Robust task queue system for downloads and maintenance
- **Admin Controls**: Comprehensive admin interface for user and provider management

## 🛠️ Tech Stack

### Backend
- **Python 3.12** - Modern Python with async/await support
- **FastAPI** - High-performance API framework with automatic OpenAPI documentation
- **PostgreSQL 16** - Robust relational database with advanced features
- **Valkey** - Redis-compatible caching and session storage
- **SQLAlchemy 2.0** - Modern ORM with async support and type safety
- **Alembic** - Database migration management
- **Pydantic** - Data validation and serialization
- **Background Tasks** - Celery-like task queue for downloads and maintenance

### Frontend
- **Vue.js 3** - Progressive JavaScript framework with Composition API
- **Tailwind CSS** - Utility-first CSS framework for rapid UI development
- **Vite** - Fast build tool and development server
- **Pinia** - State management for Vue.js applications
- **Vue Router** - Official routing library for Vue.js
- **Headless UI** - Unstyled, accessible UI components

### Infrastructure
- **Docker & Docker Compose** - Containerized deployment
- **Nginx** - Reverse proxy and static file serving
- **MailHog** - Email testing in development

## 🚀 Quick Start

### Prerequisites
- **Docker & Docker Compose** - For containerized deployment
- **Python 3.12** - For local backend development
- **Node.js 18+** - For frontend development

### Production Deployment
1. **Clone the repository**
   ```bash
   git clone https://github.com/Futs/kuroibara.git
   cd kuroibara
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and settings
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs
   - Email Testing: http://localhost:8025 (MailHog)

### Development Mode
For development with hot-reloading and debugging:

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Or use the convenience script
./dev.sh
```

### Local Frontend Development
Run the frontend separately for faster development:

```bash
cd frontend/app
npm install
npm run dev
```

### Database Setup
The application will automatically run migrations on startup. For manual migration management:

```bash
cd backend
alembic upgrade head  # Apply latest migrations
alembic revision --autogenerate -m "Description"  # Create new migration
```

## 📖 Manga Providers

Kuroibara supports 100+ manga providers, including:

### Popular Providers
- **MangaDex** - Large community-driven manga database
- **MangaPlus** - Official Shueisha manga platform
- **TCBScans** - Popular scanlation group
- **OmegaScans** - High-quality manga translations

### Specialized Providers
- **Toonily** - Manhwa and webtoons
- **ManhwaHub** - Korean manhwa focus
- **DynastyScans** - Yuri and shoujo-ai content
- **VortexScans** - Action and adventure manga

### Content Categories
- **General Manga** - Shonen, Seinen, Shoujo, Josei
- **Manhwa** - Korean webtoons and comics
- **Manhua** - Chinese comics and web novels
- **NSFW Content** - Adult content with blur controls

*For a complete list of supported providers, check the provider monitoring system in the application.*

## 🔧 Configuration

### Environment Variables
Key configuration options in `.env`:

```bash
# Database
DB_HOST=postgres
DB_USERNAME=kuroibara
DB_PASSWORD=your_password
DB_DATABASE=kuroibara

# Cache
VALKEY_HOST=valkey
VALKEY_PORT=6379

# Security
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Provider Monitoring
PROVIDER_CHECK_INTERVAL=60  # minutes
MAX_CONCURRENT_CHECKS=5
```

### Provider Health Monitoring
- **Check Intervals**: 30min, 1h, 2h, daily, weekly, monthly
- **Auto-disable**: Unhealthy providers are automatically grayed out
- **Admin Controls**: Superusers can manage provider settings
- **Statistics**: Comprehensive uptime and performance metrics

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest                    # Run all tests
pytest tests/test_api.py  # Run specific test file
pytest --cov             # Run with coverage
```

### Frontend Tests
```bash
cd frontend/app
npm test                  # Run unit tests
npm run test:e2e         # Run end-to-end tests
```

## 📚 API Documentation

The API is fully documented with OpenAPI/Swagger:
- **Interactive Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

### Key Endpoints
- `GET /api/v1/search` - Search manga across providers
- `GET /api/v1/manga/{id}` - Get manga details
- `POST /api/v1/favorites/{manga_id}` - Add to favorites
- `GET /api/v1/providers/status` - Provider health status
- `GET /api/v1/user/profile` - User profile management

## 🗺️ Development Roadmap

### Current Version: 0.1.0 (Alpha)
- ✅ Core API functionality
- ✅ Basic manga search and management
- ✅ User authentication system
- ✅ Provider health monitoring
- ✅ Docker deployment

### Planned for 0.2.0 (Beta)
- 🔄 Enhanced manga reader interface
- 🔄 Advanced search filters
- 🔄 Improved mobile responsiveness
- 🔄 Background task optimization
- 🔄 Admin dashboard enhancements

### Planned for 1.0.0 (Stable)
- 📋 Complete test coverage
- 📋 Production-ready documentation
- 📋 Performance optimizations
- 📋 Security audit and hardening
- 📋 Migration tools and guides

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for new frontend components
- Write tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **MangaDex** - For providing a robust manga API
- **Vue.js Community** - For excellent frontend framework and ecosystem
- **FastAPI** - For the high-performance backend framework
- **Scanlation Groups** - For their dedication to manga translation
