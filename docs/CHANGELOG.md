# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Additional provider integrations
- Enhanced reading analytics
- Mobile app development

## [0.5.0] - 2025-07-19

### Added
- **🔌 Template-Based Provider System**: Community members can now add new manga providers without coding
  - GitHub issue template for provider requests with comprehensive validation
  - Automated validation and testing workflow using GitHub Actions
  - Auto-PR creation for approved providers with detailed testing results
  - Community provider configuration support in dedicated directory
  - Comprehensive documentation and examples for contributors
  - CSS selector validation and testing tools
  - Provider health monitoring and automatic failover support
- **📦 Docker Hub Integration**: Official Docker images now available
  - Backend image: `futs/kuroibara-backend`
  - Frontend image: `futs/kuroibara-frontend`
  - Simplified deployment with Docker Compose
- **🔧 Storage Settings Migration**: Enhanced chapter management and storage optimization
- **📊 Enhanced Library Features**: Improved library management with advanced filtering and analytics

### Fixed
- Backend test database connection issues
- Frontend test timing and precision issues
- Duplicate storage columns in migration scripts
- Code quality improvements across backend and frontend

### Changed
- Updated to Python 3.13 for backend
- Updated to Vue.js 3.5.17 for frontend
- Updated to Tailwind CSS 4.0.0
- Improved documentation structure and organization

## [0.3.0] - 2025-01-12

### Added
- **Enhanced Filtering System**: Multi-select genre filtering with checkbox interface
- **Advanced Search Filters**: Status, type, year, content rating, and language filters
- **Smart Genre Discovery**: Find manga by combining multiple genres (e.g., Action + Adventure)
- **Content Filtering**: Safe/NSFW content filtering with granular controls
- **Visual Filter Management**: Individual removable filter tags with clear options
- **Hybrid Filtering**: Backend + client-side filtering for optimal performance

### Fixed
- **MangaDex Genre Extraction**: Fixed genre extraction by including "tag" in API includes parameter
- **Multi-Genre Logic**: Implemented AND logic for multiple genre selection
- **Filter State Management**: Proper state persistence during provider browsing

### Improved
- **Provider Explorer UI**: Enhanced filtering interface with responsive two-row layout
- **User Experience**: Real-time filtering with immediate visual feedback
- **Performance**: Optimized filtering with debounced search and efficient client-side processing

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
