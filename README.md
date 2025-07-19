[![GitHub Release](https://img.shields.io/github/v/release/Futs/kuroibara?label=version)](https://github.com/Futs/kuroibara/releases)
[![Docker Backend](https://img.shields.io/docker/pulls/futs/kuroibara-backend?label=backend%20pulls)](https://hub.docker.com/r/futs/kuroibara-backend)
[![Docker Frontend](https://img.shields.io/docker/pulls/futs/kuroibara-frontend?label=frontend%20pulls)](https://hub.docker.com/r/futs/kuroibara-frontend)
[![GitHub Stars](https://img.shields.io/github/stars/Futs/kuroibara)](https://github.com/Futs/kuroibara/stargazers)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

# Kuroibara <img src="frontend/app/public/assets/logo/logo.png" alt="Kuroibara Logo" width="32" height="32">

A modern manga management platform for discovering, organizing, and reading manga from 80+ online sources.

> **🚀 Latest Release**: v0.5.0 with Storage Settings Migration and Enhanced Chapter Management

## ✨ Features

- 🔍 **80+ Manga Providers** - MangaDex, MangaPlus, TCBScans, and more
- 📚 **Smart Library** - Personal collection with automatic metadata
- 📖 **Advanced Reader** - Multiple reading modes, bookmarks, progress tracking
- 🎨 **Customizable UI** - Dark/light themes, responsive design
- 🔐 **Secure Authentication** - 2FA support, external account linking
- ☁️ **Cloudflare Bypass** - Optional FlareSolverr integration
- 📊 **Reading Analytics** - Statistics, streaks, achievements
- 🎯 **Smart Filtering** - Genre, status, year, content rating filters

## 🛠️ Tech Stack

- **Backend**: Python 3.13, FastAPI, PostgreSQL, Redis
- **Frontend**: Vue.js 3, Tailwind CSS 4, Vite
- **Infrastructure**: Docker, Nginx

## 🚀 Quick Start

### 🐳 Docker Hub (Recommended)

```bash
# Pull and run with Docker Compose
curl -O https://raw.githubusercontent.com/Futs/kuroibara/main/docker-compose.yml
docker compose up -d
```

**Docker Images:**
- **Backend**: [`futs/kuroibara-backend`](https://hub.docker.com/r/futs/kuroibara-backend)
- **Frontend**: [`futs/kuroibara-frontend`](https://hub.docker.com/r/futs/kuroibara-frontend)

### 📦 From Source

```bash
git clone https://github.com/Futs/kuroibara.git
cd kuroibara
cp .env.example .env
docker compose up -d
```

### 🌐 Access

- **Application**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## 🔓 Optional: FlareSolverr Integration

Bypass Cloudflare protection for additional providers:

```bash
docker run -d --name flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest
echo "FLARESOLVERR_URL=http://localhost:8191" >> .env
docker compose restart backend
```

📖 [Complete Setup Guide](docs/FLARESOLVERR_SETUP.md)

## 📚 Documentation

- 📖 [GitHub Wiki](https://github.com/Futs/kuroibara/wiki) - User guides and tutorials
- 🔧 [Technical Docs](docs/README.md) - Development and API documentation
- 🚀 [Getting Started](https://github.com/Futs/kuroibara/wiki/Getting-Started) - Setup guide
- 🐛 [Troubleshooting](https://github.com/Futs/kuroibara/wiki/Troubleshooting) - Common issues

## 🤝 Contributing

- 🐛 [Report Issues](https://github.com/Futs/kuroibara/issues/new) - Found a bug?
- 💡 [Feature Requests](https://github.com/Futs/kuroibara/issues/new) - Suggest improvements
- 🔌 [Add Providers](docs/TEMPLATE_PROVIDER_SYSTEM.md) - No coding required!
- 🏗️ [Development Guide](docs/DEVELOPMENT.md) - For developers

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Kuroibara** - Modern manga management for enthusiasts worldwide.
