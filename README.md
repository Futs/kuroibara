<!-- Build & Deployment Status -->
[![PR Checks](https://github.com/Futs/kuroibara/actions/workflows/pr-checks.yml/badge.svg?branch=main)](https://github.com/Futs/kuroibara/actions/workflows/pr-checks.yml)
[![Deploy](https://github.com/Futs/kuroibara/actions/workflows/deploy.yml/badge.svg?branch=main)](https://github.com/Futs/kuroibara/actions/workflows/deploy.yml)
[![Security Scan](https://github.com/Futs/kuroibara/actions/workflows/security-scan.yml/badge.svg?branch=main)](https://github.com/Futs/kuroibara/actions/workflows/security-scan.yml)

<!-- Project Stats -->
[![GitHub Release](https://img.shields.io/github/v/release/Futs/kuroibara?include_prereleases&label=version)](https://github.com/Futs/kuroibara/releases)
[![GitHub Issues](https://img.shields.io/github/issues/Futs/kuroibara)](https://github.com/Futs/kuroibara/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/Futs/kuroibara)](https://github.com/Futs/kuroibara/pulls)
[![GitHub Stars](https://img.shields.io/github/stars/Futs/kuroibara)](https://github.com/Futs/kuroibara/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/Futs/kuroibara)](https://github.com/Futs/kuroibara/network/members)
[![GitHub Last Commit](https://img.shields.io/github/last-commit/Futs/kuroibara)](https://github.com/Futs/kuroibara/commits/main)

<!-- Tech Stack -->
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/node.js-22-green.svg)](https://nodejs.org/)
[![Vue.js](https://img.shields.io/badge/vue.js-3.5.13-4FC08D.svg)](https://vuejs.org/)
[![Tailwind CSS](https://img.shields.io/badge/tailwind-4.0.0-38B2AC.svg)](https://tailwindcss.com/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://www.docker.com/)

<!-- Code Quality & License -->
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub Repo Size](https://img.shields.io/github/repo-size/Futs/kuroibara)](https://github.com/Futs/kuroibara)
[![GitHub Language Count](https://img.shields.io/github/languages/count/Futs/kuroibara)](https://github.com/Futs/kuroibara)
[![GitHub Top Language](https://img.shields.io/github/languages/top/Futs/kuroibara)](https://github.com/Futs/kuroibara)

<!-- Additional Project Health Metrics -->
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/Futs/kuroibara/pr-checks.yml?branch=main&label=tests)](https://github.com/Futs/kuroibara/actions/workflows/pr-checks.yml)
[![GitHub Commit Activity](https://img.shields.io/github/commit-activity/m/Futs/kuroibara)](https://github.com/Futs/kuroibara/graphs/commit-activity)
[![GitHub Contributors](https://img.shields.io/github/contributors/Futs/kuroibara)](https://github.com/Futs/kuroibara/graphs/contributors)

# Kuroibara (Black Rose) <img src="frontend/app/public/assets/logo/logo.png" alt="Kuroibara Logo" width="32" height="32">

A modern, full-featured web application for manga, manhua, and manhwa enthusiasts. Kuroibara provides a comprehensive platform for discovering, managing, and reading manga from multiple online sources.

> **⚠️ Development Status**: Kuroibara is currently in active development (v0.2.0). While the core features are functional, expect regular updates and potential breaking changes until v1.0.0 release.

## ✨ Key Features

- **Multi-Provider Search**: Access 80+ manga providers including MangaDex, MangaPlus, TCBScans, and more
- **Enhanced Filtering**: Multi-select genre filtering, status, type, year, content rating, and language filters
- **Smart Discovery**: Find manga by combining multiple criteria (e.g., Action + Adventure + Ongoing)
- **Cloudflare Bypass**: Optional FlareSolverr integration for accessing Cloudflare-protected providers
- **Smart Library Management**: Personal library with automatic metadata and cover art
- **Background Downloads**: Queue and download manga chapters with background processing
- **Content Filtering**: Safe/NSFW content filtering with granular controls
- **User Profiles**: Customizable profiles with external account linking (AniList, MyAnimeList)
- **Provider Health Monitoring**: Real-time monitoring with automatic status updates
- **2FA Authentication**: Secure user registration and login
- **Dark/Light Theme**: Modern responsive design with system theme support and quick toggle
- **Responsive Design**: Modern Vue.js interface with Tailwind CSS 4.0

### 📖 Advanced Reading Experience

- **Multiple Reading Modes**:
  - **Single Page**: Traditional page-by-page reading
  - **Double-Page Spread**: Side-by-side pages for manga spreads
  - **List View**: Continuous scrolling for webtoons and long-strip content
  - **Adaptive Mode**: Intelligent content detection that auto-selects optimal reading mode
- **Advanced Image Handling**:
  - Multiple fit modes (width, height, both, original size)
  - Quality settings for different network conditions (high/medium/low)
  - Smart image preloading (configurable 1-10 pages ahead)
  - Memory management with automatic cleanup
- **Comprehensive Keyboard Shortcuts**: Full keyboard navigation and control
- **Reading Direction Support**: RTL/LTR with proper double-page handling

### 📊 Reading Progress & Analytics

- **Reading Statistics**: Track time spent, pages read, and reading sessions
- **Smart Bookmarking**: Bookmark specific pages with notes and quick access
- **Resume Reading**: Intelligent resume from last position across sessions
- **Reading Streaks**: Track consecutive reading days with achievement system
- **Achievement System**: Unlock achievements for reading milestones and goals
- **Analytics Dashboard**: Comprehensive reading statistics and progress visualization
- **Reading History**: Detailed session history with timestamps and progress

### 🎨 Interface & Customization

- **Custom Color Themes**: Predefined themes (Dark, Light, Sepia, Night) with full customization
- **Typography Control**: Font family, size, line height, and letter spacing adjustments
- **UI Layout Options**: Multiple layout presets (Default, Minimal, Immersive, Sidebar, Bottom)
- **Display Customization**: Page margins, padding, border radius, shadows, and transitions
- **Theme Management**: Export/import themes, real-time preview, and reset options
- **Advanced Styling**: CSS custom properties integration for dynamic theming

## 🛠️ Tech Stack

**Backend**: Python 3.12+, FastAPI 0.115+, PostgreSQL 16, Valkey (Redis), SQLAlchemy 2.0
**Frontend**: Vue.js 3.5, Tailwind CSS 4.0, Vite 6.3, Pinia 3.0, Node.js 22
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

## 🔓 FlareSolverr Integration (Optional)

Kuroibara supports optional integration with [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) to bypass Cloudflare protection and access additional manga providers.

### Quick Setup
```bash
# Run FlareSolverr
docker run -d --name flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest

# Configure Kuroibara
echo "FLARESOLVERR_URL=http://localhost:8191" >> .env

# Restart Kuroibara
docker compose restart backend
```

**Result**: Unlocks 4+ additional Cloudflare-protected providers (ReaperScans, MangaFire, etc.)

📖 **[Complete FlareSolverr Setup Guide](docs/FLARESOLVERR_SETUP.md)** - Detailed installation and configuration instructions

## 📚 Documentation

### 📖 **User Documentation**
- **[📖 GitHub Wiki](https://github.com/Futs/kuroibara/wiki)** - User guides, tutorials, and troubleshooting
- **[🚀 Getting Started](https://github.com/Futs/kuroibara/wiki/Getting-Started)** - Complete setup guide for new users
- **[📱 User Guide](https://github.com/Futs/kuroibara/wiki/User-Guide)** - How to use all Kuroibara features
- **[🔧 Installation](https://github.com/Futs/kuroibara/wiki/Installation)** - Step-by-step installation instructions
- **[🐛 Troubleshooting](https://github.com/Futs/kuroibara/wiki/Troubleshooting)** - Common issues and solutions

### 🔧 **Technical Documentation**
- **[📋 Technical Docs](docs/README.md)** - Complete technical documentation index
- **[🏗️ Development Guide](docs/DEVELOPMENT.md)** - Development environment and contributing
- **[⚙️ Configuration](docs/CONFIGURATION.md)** - System configuration and environment variables
- **[🔌 API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[🌐 Providers](docs/PROVIDERS.md)** - Provider system and supported sources

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### **For Users**
- **[📖 Wiki Contributions](https://github.com/Futs/kuroibara/wiki/Contributing-Wiki)** - Help improve user documentation
- **[🐛 Report Issues](https://github.com/Futs/kuroibara/issues/new)** - Found a bug? Let us know!
- **[💡 Feature Requests](https://github.com/Futs/kuroibara/issues/new)** - Suggest new features

### **For Developers**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### **For Provider Contributors** 🔌
Want to add a new manga provider? No coding required!
1. **[📝 Submit a Provider Request](https://github.com/Futs/kuroibara/issues/new?template=provider-request.yml)** - Fill out our simple template
2. **🤖 Automatic Validation** - Our system tests your provider automatically
3. **🔄 Auto-PR Creation** - If validation passes, a PR is created automatically
4. **✅ Review & Merge** - Maintainers review and merge to add your provider

See our **[🔌 Template Provider System Guide](docs/TEMPLATE_PROVIDER_SYSTEM.md)** for detailed instructions.

See our **[🏗️ Development Guide](docs/DEVELOPMENT.md)** and **[📋 Git Guidelines](docs/GIT_GUIDELINES.md)** for detailed contributing guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Kuroibara** - A comprehensive manga management platform for enthusiasts worldwide.
