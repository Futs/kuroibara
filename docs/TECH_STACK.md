# Tech Stack Details

## Backend Technologies

### Core Framework
- **Python 3.13** - Latest Python with enhanced performance and async/await support
- **FastAPI 0.115+** - High-performance API framework with automatic OpenAPI documentation
- **Uvicorn** - Lightning-fast ASGI server for production deployment

### Database & Storage
- **PostgreSQL 16** - Robust relational database with advanced features
  - JSON/JSONB support for flexible data structures
  - Full-text search capabilities
  - Advanced indexing and query optimization
- **Valkey** - Redis-compatible caching and session storage
  - Session management and user authentication
  - Background task queue storage
  - Provider health status caching

### ORM & Data Management
- **SQLAlchemy 2.0** - Modern ORM with async support and type safety
  - Declarative models with type hints
  - Async query execution
  - Advanced relationship management
- **Alembic** - Database migration management
  - Version-controlled schema changes
  - Automatic migration generation
  - Rollback capabilities

### Data Validation & Serialization
- **Pydantic** - Data validation and serialization
  - Type-safe API models
  - Automatic request/response validation
  - Configuration management

### Background Processing
- **Background Tasks** - Celery-like task queue for downloads and maintenance
  - Manga chapter downloads
  - Provider health checks
  - Database maintenance tasks
  - Email notifications

## Frontend Technologies

### Core Framework
- **Vue.js 3.5.17** - Progressive JavaScript framework with Composition API
  - Reactive data binding
  - Component-based architecture
  - TypeScript support
  - Excellent performance

### Styling & UI
- **Tailwind CSS 4.0.0** - Utility-first CSS framework for rapid UI development
  - Responsive design utilities
  - Dark mode support
  - Custom component styling
- **Headless UI** - Unstyled, accessible UI components
  - Fully accessible components
  - Keyboard navigation support
  - Screen reader compatibility

### Build Tools & Development
- **Vite** - Fast build tool and development server
  - Hot module replacement (HMR)
  - Optimized production builds
  - Plugin ecosystem
- **TypeScript** - Type-safe JavaScript development
  - Enhanced IDE support
  - Compile-time error checking
  - Better code documentation

### State Management & Routing
- **Pinia** - State management for Vue.js applications
  - Intuitive API design
  - TypeScript support
  - DevTools integration
- **Vue Router** - Official routing library for Vue.js
  - Nested routing
  - Route guards
  - Dynamic route matching

## Infrastructure & DevOps

### Containerization
- **Docker** - Application containerization
  - Multi-stage builds for optimization
  - Development and production configurations
  - Consistent deployment environments
- **Docker Compose** - Multi-container application orchestration
  - Service dependency management
  - Environment-specific configurations
  - Volume and network management

### Web Server & Proxy
- **Nginx** - Reverse proxy and static file serving
  - Load balancing capabilities
  - SSL/TLS termination
  - Static asset optimization
  - Request routing and filtering

### Development Tools
- **MailHog** - Email testing in development
  - SMTP server simulation
  - Web-based email viewer
  - Email debugging capabilities

## Security & Authentication

### Authentication & Authorization
- **JWT (JSON Web Tokens)** - Stateless authentication
  - Secure token-based authentication
  - Configurable expiration times
  - Refresh token support
- **2FA (Two-Factor Authentication)** - Enhanced security
  - TOTP (Time-based One-Time Password)
  - QR code generation for authenticator apps
  - Backup codes for account recovery

### Security Features
- **Password Hashing** - Secure password storage using bcrypt
- **CORS (Cross-Origin Resource Sharing)** - Controlled cross-origin requests
- **Rate Limiting** - API endpoint protection
- **Input Validation** - Comprehensive request validation
- **SQL Injection Prevention** - ORM-based query protection

## Development & Testing

### Code Quality
- **Black** - Python code formatting
- **isort** - Import statement organization
- **Flake8** - Python linting and style checking
- **mypy** - Static type checking for Python

### Testing Frameworks
- **pytest** - Python testing framework
  - Fixture-based testing
  - Parametrized tests
  - Coverage reporting
- **Vitest** - Frontend testing framework
  - Unit testing for Vue components
  - Mock and spy utilities
  - Snapshot testing

### API Documentation
- **OpenAPI/Swagger** - Automatic API documentation
  - Interactive API explorer
  - Request/response examples
  - Schema validation documentation
- **ReDoc** - Alternative API documentation viewer
  - Clean, responsive design
  - Advanced search capabilities
  - Code examples in multiple languages

## Performance & Monitoring

### Caching Strategy
- **Application-level caching** - Valkey/Redis for frequently accessed data
- **Database query optimization** - Efficient SQLAlchemy queries
- **Static asset caching** - Nginx-based static file caching

### Monitoring & Logging
- **Provider Health Monitoring** - Real-time provider status tracking
- **Application logging** - Structured logging with configurable levels
- **Performance metrics** - Response time and throughput monitoring

## Scalability Considerations

### Horizontal Scaling
- **Stateless application design** - Easy horizontal scaling
- **Database connection pooling** - Efficient database resource usage
- **Background task distribution** - Scalable task processing

### Performance Optimization
- **Async/await patterns** - Non-blocking I/O operations
- **Database indexing** - Optimized query performance
- **CDN-ready static assets** - Optimized asset delivery
