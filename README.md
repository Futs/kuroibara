[![Deploy](https://github.com/Futs/kuroibara/actions/workflows/deploy.yml/badge.svg)](https://github.com/Futs/kuroibara/actions/workflows/deploy.yml)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/Futs/kuroibara/releases)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Vue.js](https://img.shields.io/badge/vue.js-3.5-4FC08D.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-latest-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub Issues](https://img.shields.io/github/issues/Futs/kuroibara.svg)](https://github.com/Futs/kuroibara/issues)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Kuroibara (Black Rose) <img src="frontend/app/public/assets/logo/logo.png" alt="Kuroibara Logo" width="32" height="32">

A modern, full-featured web application for manga, manhua, and manhwa enthusiasts. Kuroibara provides a comprehensive platform for discovering, managing, and reading manga from multiple online sources.

> **⚠️ Development Status**: Kuroibara is currently in active development (v0.1.0). While the core features are functional, expect regular updates and potential breaking changes until v1.0.0 release.

## ✨ Key Features

- **Multi-Provider Search**: Access 100+ manga providers including MangaDex, MangaPlus, TCBScans, and more
- **Smart Library Management**: Personal library with automatic metadata and cover art
- **Background Downloads**: Queue and download manga chapters with background processing
- **User Profiles**: Customizable profiles with external account linking (AniList, MyAnimeList)
- **Provider Health Monitoring**: Real-time monitoring with automatic status updates
- **2FA Authentication**: Secure user registration and login
- **Responsive Design**: Modern Vue.js interface with Tailwind CSS

## 🛠️ Tech Stack

**Backend**: Python 3.12, FastAPI, PostgreSQL 16, Valkey (Redis), SQLAlchemy 2.0
**Frontend**: Vue.js 3, Tailwind CSS, Vite, Pinia
**Infrastructure**: Docker & Docker Compose, Nginx

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+ (for local development)
- Node.js 22+ (for frontend development)

### Production Deployment
```bash
# Clone and setup
git clone https://github.com/Futs/kuroibara.git
cd kuroibara
cp .env.example .env
# Edit .env with your settings

# Start the application
docker compose up -d
```

### Development Mode
```bash
# Start development environment
docker compose -f docker-compose.dev.yml up -d
# Or use the convenience script
./dev.sh
```

### Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Email Testing**: http://localhost:8025 (MailHog)

## � Documentation

- **[Tech Stack Details](docs/TECH_STACK.md)** - Comprehensive technology overview
- **[Configuration Guide](docs/CONFIGURATION.md)** - Environment setup and configuration
- **[API Documentation](docs/API_REFERENCE.md)** - Complete API reference and examples
- **[Provider Information](docs/PROVIDERS.md)** - Supported manga providers and details
- **[Development Guide](docs/DEVELOPMENT.md)** - Testing, contributing, and development setup
- **[Roadmap](docs/ROADMAP.md)** - Development roadmap and planned features

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [Development Guide](docs/DEVELOPMENT.md) for detailed contributing guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Kuroibara** - A comprehensive manga management platform for enthusiasts worldwide.
