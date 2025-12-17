[![PR Checks](https://github.com/Futs/kuroibara/actions/workflows/pr-checks.yml/badge.svg?branch=main)](https://github.com/Futs/kuroibara/actions/workflows/pr-checks.yml)
[![Deploy](https://github.com/Futs/kuroibara/actions/workflows/deploy.yml/badge.svg?branch=main)](https://github.com/Futs/kuroibara/actions/workflows/deploy.yml)
[![Security Scan](https://github.com/Futs/kuroibara/actions/workflows/security-scan.yml/badge.svg?branch=main)](https://github.com/Futs/kuroibara/actions/workflows/security-scan.yml)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/Futs/kuroibara/pr-checks.yml?branch=main&label=tests)](https://github.com/Futs/kuroibara/actions/workflows/pr-checks.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/Futs/kuroibara)](https://github.com/Futs/kuroibara/stargazers)

# Kuroibara <img src="frontend/app/public/assets/logo/logo.png" alt="Kuroibara Logo" width="32" height="32">

A modern manga management platform for discovering, organizing, and reading manga from multiple online sources. Built with reliability and performance in mind.

[![GitHub Release](https://img.shields.io/github/v/release/Futs/kuroibara?label=version)](https://github.com/Futs/kuroibara/releases)

> **📦 Latest Release**: v0.7.0 with Enhanced Architecture & Job System
> **🚧 Development Branch**: `index/download` - Advanced Reader Features & UI Improvements


## ✨ Features

![Providers](https://img.shields.io/badge/Providers-11+-blue)
![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-green)
![Authentication](https://img.shields.io/badge/Auth-Role--based-orange)
![Themes](https://img.shields.io/badge/Themes-Dark%2FLight-purple)

### Core Features
- **Personal Library** - Organize your manga collection with automatic metadata
- **Multi-Provider Search** - Search across 11+ manga sources simultaneously
- **Batch Downloads** - Download entire series with progress tracking and retry logic
- **Modern Interface** - Clean, responsive design with dark/light themes
- **User Management** - Secure authentication with role-based access
- **Advanced Filtering** - Filter by genre, status, year, and content rating
- **Cloudflare Support** - Optional FlareSolverr integration for protected sites
- **Background Tasks** - Automated health checks and maintenance
- **Real-time Updates** - Live progress notifications via WebSocket

### 📖 Advanced Reader Features (New!)
- **Professional Reading Experience** - Feature-rich manga reader with multiple viewing modes
- **Flexible Zoom Controls** - Zoom in/out (25%-500%), mouse wheel zoom, keyboard shortcuts
- **Multiple Fit Modes** - Width, Height, Both, Original size with instant switching
- **Reading Modes** - Single page, double page, list view, adaptive, and webtoon modes
- **Fullscreen Support** - Immersive reading with F11 or dedicated button
- **Smart Navigation** - Keyboard shortcuts, click zones, chapter selector
- **Bookmarks & Progress** - Save favorite pages with notes, automatic progress tracking
- **Reading Statistics** - Track reading time, pages read, streaks, and achievements
- **Customizable Themes** - Dark, light, sepia, and custom color schemes
- **UI Layouts** - Default, minimal, and immersive layouts
- **Display Options** - Adjustable margins, border radius, and opacity
- **Perfect Scrolling** - Smooth scroll behavior with proper zoom support
- **Keyboard Shortcuts** - Comprehensive keyboard controls for power users


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
- **Architecture**: Agent-based providers, Job queue system, Health monitoring
- **Real-time**: WebSocket support, Progress tracking, Live updates

## 🚀 Quick Start

### 🐳 Docker Hub (Recommended)

```bash
# Pull and run with Docker Compose
curl -O https://raw.githubusercontent.com/Futs/kuroibara/main/docker-compose.yml
docker compose up -d
```

**Docker Images:**
- **Backend**:  
[![Docker Backend](https://img.shields.io/docker/pulls/futs/kuroibara-backend?label=backend%20pulls)](https://hub.docker.com/r/futs/kuroibara-backend)  
- **Frontend**:  
[![Docker Frontend](https://img.shields.io/docker/pulls/futs/kuroibara-frontend?label=frontend%20pulls)](https://hub.docker.com/r/futs/kuroibara-frontend) 

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
- **Job Queue API**: http://localhost:8000/docs#/Jobs
- **Health Monitoring**: http://localhost:8000/docs#/Health%20Monitoring
- **Agent Management**: http://localhost:8000/docs#/Agents
- **Progress Tracking**: http://localhost:8000/docs#/Progress

## 🔓 Optional: FlareSolverr Integration

Bypass Cloudflare protection for additional providers:

```bash
docker run -d --name flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest
echo "FLARESOLVERR_URL=http://localhost:8191" >> .env
docker compose restart backend
```

📖 [Complete Setup Guide](docs/FLARESOLVERR_SETUP.md)

## 🏗️ Architecture

Kuroibara is built with a modern, reliable architecture:

- 🤖 **Smart Provider System** - Intelligent manga provider management with health monitoring
- 📋 **Job Queue** - Priority-based download and task scheduling
- ⚡ **Rate Limiting** - Optimized request handling for each provider
- 📊 **Real-time Updates** - Live progress tracking with WebSocket support
- 🛡️ **Fault Tolerance** - Provider failures don't affect other providers

� **[Technical Details](docs/ARCHITECTURE.md)** - Complete architecture documentation

## 📚 Documentation

- 📖 [GitHub Wiki](https://github.com/Futs/kuroibara/wiki) - User guides and tutorials
- 🚀 [Getting Started](https://github.com/Futs/kuroibara/wiki/Getting-Started) - Setup guide
- � [Technical Docs](docs/README.md) - Development and API documentation
- � [Troubleshooting](https://github.com/Futs/kuroibara/wiki/Troubleshooting) - Common issues

## 🤝 Contributing

- 🐛 [Report Issues](https://github.com/Futs/kuroibara/issues/new) - Found a bug?
- 💡 [Feature Requests](https://github.com/Futs/kuroibara/issues/new) - Suggest improvements
- 🔌 [Add Providers](docs/TEMPLATE_PROVIDER_SYSTEM.md) - No coding required!
- 🏗️ [Development Guide](docs/DEVELOPMENT.md) - For developers

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Kuroibara** - Modern manga management for enthusiasts worldwide.

## 🤖 Repo Statistics
![Alt](https://repobeats.axiom.co/api/embed/f25e543ba7457e8ca5c622072e11becd5e6e2cd4.svg "Repobeats analytics image")