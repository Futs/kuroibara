[![PR Checks](https://github.com/Futs/kuroibara/actions/workflows/pr-checks.yml/badge.svg?branch=main)](https://github.com/Futs/kuroibara/actions/workflows/pr-checks.yml)
[![Deploy](https://github.com/Futs/kuroibara/actions/workflows/deploy.yml/badge.svg?branch=main)](https://github.com/Futs/kuroibara/actions/workflows/deploy.yml)
[![Security Scan](https://github.com/Futs/kuroibara/actions/workflows/security-scan.yml/badge.svg?branch=main)](https://github.com/Futs/kuroibara/actions/workflows/security-scan.yml)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/Futs/kuroibara/pr-checks.yml?branch=main&label=tests)](https://github.com/Futs/kuroibara/actions/workflows/pr-checks.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/Futs/kuroibara)](https://github.com/Futs/kuroibara/stargazers)

# Kuroibara <img src="frontend/app/public/assets/logo/logo.png" alt="Kuroibara Logo" width="32" height="32">

A modern manga management platform for discovering, organizing, and reading manga from multiple online sources.

> [![GitHub Release](https://img.shields.io/github/v/release/Futs/kuroibara?label=version)](https://github.com/Futs/kuroibara/releases)

> **🚀 Latest Release**: v0.6.0 with Enhanced Testing
> 

## ✨ Features

- 📚 **Smart Library** - Personal collection with automatic metadata
- 📖 **Advanced Reader** - Multiple reading modes, bookmarks, progress tracking
- 🎨 **Customizable UI** - Dark/light themes, responsive design
- 🔐 **Secure Authentication** - 2FA support, external account linking
- ☁️ **Cloudflare Bypass** - Optional FlareSolverr integration
- 📊 **Reading Analytics** - Statistics, streaks, achievements
- 🎯 **Smart Filtering** - Genre, status, year, content rating filters

## 🛠️ Tech Stack
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/node.js-22-green.svg)](https://nodejs.org/)
[![Vue.js](https://img.shields.io/badge/vue.js-3.5.17-4FC08D.svg)](https://vuejs.org/)
[![Tailwind CSS](https://img.shields.io/badge/tailwind-4.0.0-38B2AC.svg)](https://tailwindcss.com/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://www.docker.com/)

- **Backend**: Python 3.13, FastAPI, PostgreSQL, Valkey (Redis fork)
- **Frontend**: Vue.js 3.5.17, Tailwind CSS 4, Vite 6
- **Infrastructure**: Docker, Nginx

## 🚀 Quick Start

### 🐳 Docker Hub (Recommended)

```bash
# Pull and run with Docker Compose
curl -O https://raw.githubusercontent.com/Futs/kuroibara/main/docker-compose.yml
docker compose up -d
```

**Docker Images:**
> **Backend**:
> [![Docker Backend](https://img.shields.io/docker/pulls/futs/kuroibara-backend?label=backend%20pulls)](https://hub.docker.com/r/futs/kuroibara-backend)
> **Frontend**:
> [![Docker Frontend](https://img.shields.io/docker/pulls/futs/kuroibara-frontend?label=frontend%20pulls)](https://hub.docker.com/r/futs/kuroibara-frontend)

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
