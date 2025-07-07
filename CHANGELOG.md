# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Enhanced manga reader interface
- Advanced search filters and sorting
- Improved mobile responsiveness
- Background task optimization
- Admin dashboard enhancements

### Changed
- Updated provider health monitoring system
- Improved API response times
- Enhanced user interface components

### Fixed
- Various bug fixes and stability improvements

## [0.1.0] - 2025-07-07

### Added
- Initial release of Kuroibara manga platform
- Core API functionality with FastAPI
- User authentication and authorization system
- Multi-provider manga search (100+ providers)
- Personal library management
- Provider health monitoring system
- Background task processing
- Docker containerization
- Vue.js frontend with Tailwind CSS
- PostgreSQL database with Alembic migrations
- Valkey (Redis) caching layer
- Comprehensive admin controls
- NSFW content filtering
- User profiles with external account linking
- Favorites and bookmarking system
- Responsive web design
- API documentation with OpenAPI/Swagger
- Development and production Docker configurations
- Automated versioning system
- CI/CD pipeline with GitHub Actions

### Technical Details
- Python 3.12 backend with async/await support
- FastAPI framework with automatic validation
- Vue.js 3 with Composition API
- SQLAlchemy 2.0 ORM with type safety
- Pydantic data validation
- Tailwind CSS utility framework
- Vite build tool and dev server
- Docker multi-stage builds
- Environment-based configuration
- Structured logging and monitoring

### Known Issues
- Some provider integrations may be unstable
- Mobile interface needs optimization
- Admin dashboard requires UX improvements
- Background task monitoring needs enhancement

[Unreleased]: https://github.com/Futs/kuroibara/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Futs/kuroibara/releases/tag/v0.1.0
