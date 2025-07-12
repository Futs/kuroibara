# Development Guide

## Getting Started

### Prerequisites
- **Python 3.12+** - Backend development
- **Node.js 18+** - Frontend development
- **Docker & Docker Compose** - Containerized development
- **Git** - Version control
- **PostgreSQL** - Database (or use Docker)
- **Valkey/Redis** - Cache (or use Docker)

### Development Environment Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/Futs/kuroibara.git
cd kuroibara
```

#### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with development settings
DEBUG=true
ENVIRONMENT=development
DB_HOST=localhost  # or postgres for Docker
VALKEY_HOST=localhost  # or valkey for Docker
```

#### 3. Docker Development Setup (Recommended)
```bash
# Start development environment
docker compose -f docker-compose.dev.yml up -d

# Or use the convenience script
./dev.sh

# View logs
docker compose -f docker-compose.dev.yml logs -f
```

#### 4. Local Development Setup
```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Database setup
alembic upgrade head

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend setup (new terminal)
cd frontend/app
npm install
npm run dev
```

## Project Structure

```
kuroibara/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core functionality
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── main.py         # FastAPI application
│   ├── alembic/            # Database migrations
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # Vue.js frontend
│   └── app/
│       ├── src/
│       │   ├── components/ # Vue components
│       │   ├── views/      # Page components
│       │   ├── stores/     # Pinia stores
│       │   ├── router/     # Vue Router
│       │   └── main.ts     # Application entry
│       ├── public/         # Static assets
│       └── package.json    # Node.js dependencies
├── docs/                   # Documentation
├── .github/                # GitHub workflows
└── docker-compose*.yml     # Docker configurations
```

## Backend Development

### Code Style and Formatting
```bash
# Install development tools
pip install black isort flake8 mypy pytest

# Format code
black app/
isort app/

# Lint code
flake8 app/
mypy app/

# Run all checks
./scripts/lint.sh
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

### Adding New API Endpoints
```python
# app/api/v1/endpoints/example.py
from fastapi import APIRouter, Depends
from app.schemas.example import ExampleCreate, ExampleResponse
from app.services.example import ExampleService

router = APIRouter()

@router.post("/", response_model=ExampleResponse)
async def create_example(
    example: ExampleCreate,
    service: ExampleService = Depends()
):
    return await service.create(example)
```

### Database Models
```python
# app/models/example.py
from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base

class Example(Base):
    __tablename__ = "examples"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Pydantic Schemas
```python
# app/schemas/example.py
from pydantic import BaseModel
from datetime import datetime

class ExampleBase(BaseModel):
    name: str

class ExampleCreate(ExampleBase):
    pass

class ExampleResponse(ExampleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
```

## Frontend Development

### Code Style and Formatting
```bash
# Install development tools
npm install -D eslint prettier @typescript-eslint/parser

# Format code
npm run format

# Lint code
npm run lint

# Type check
npm run type-check
```

### Vue Component Structure
```vue
<!-- src/components/ExampleComponent.vue -->
<template>
  <div class="example-component">
    <h2>{{ title }}</h2>
    <button @click="handleClick">Click me</button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  title: string
}

const props = defineProps<Props>()
const count = ref(0)

const handleClick = () => {
  count.value++
}
</script>

<style scoped>
.example-component {
  @apply p-4 bg-white rounded-lg shadow;
}
</style>
```

### Pinia Store
```typescript
// src/stores/example.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useExampleStore = defineStore('example', () => {
  const items = ref<Item[]>([])
  const loading = ref(false)

  const fetchItems = async () => {
    loading.value = true
    try {
      const response = await api.getItems()
      items.value = response.data
    } finally {
      loading.value = false
    }
  }

  return {
    items,
    loading,
    fetchItems
  }
})
```

## Testing

### Backend Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_create_user
```

### Test Structure
```python
# tests/test_example.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_example():
    response = client.post(
        "/api/v1/examples/",
        json={"name": "Test Example"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Example"

@pytest.fixture
def example_data():
    return {"name": "Test Example"}
```

### Frontend Testing
```bash
# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run end-to-end tests
npm run test:e2e

# Run tests in watch mode
npm run test:watch
```

### Vue Component Testing
```typescript
// tests/components/ExampleComponent.test.ts
import { mount } from '@vue/test-utils'
import ExampleComponent from '@/components/ExampleComponent.vue'

describe('ExampleComponent', () => {
  it('renders title correctly', () => {
    const wrapper = mount(ExampleComponent, {
      props: { title: 'Test Title' }
    })
    
    expect(wrapper.text()).toContain('Test Title')
  })

  it('handles click events', async () => {
    const wrapper = mount(ExampleComponent, {
      props: { title: 'Test' }
    })
    
    await wrapper.find('button').trigger('click')
    // Add assertions for click behavior
  })
})
```

## Contributing Guidelines

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and commit
git add .
git commit -m "feat: add amazing feature"

# Push to origin
git push origin feature/amazing-feature

# Create pull request on GitHub
```

### Commit Message Convention
```
type(scope): description

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes
- refactor: Code refactoring
- test: Test changes
- chore: Build/tooling changes

Examples:
feat(api): add manga search endpoint
fix(ui): resolve mobile navigation issue
docs(readme): update installation instructions
```

### Code Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No breaking changes (or properly documented)
- [ ] Security considerations addressed
- [ ] Performance impact considered

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## Debugging

### Backend Debugging
```python
# Add debug logging
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")

# Use debugger
import pdb; pdb.set_trace()

# Or with ipdb for better experience
import ipdb; ipdb.set_trace()
```

### Frontend Debugging
```typescript
// Console debugging
console.log('Debug info:', data)
console.error('Error:', error)

// Vue DevTools
// Install Vue DevTools browser extension

// Network debugging
// Use browser DevTools Network tab
```

### Docker Debugging
```bash
# View container logs
docker compose logs -f app

# Execute commands in container
docker compose exec app bash

# Debug specific service
docker compose up app --build
```

## Performance Optimization

### Backend Optimization
- Use async/await for I/O operations
- Implement database query optimization
- Add caching with Valkey/Redis
- Use connection pooling
- Profile with cProfile or py-spy

### Frontend Optimization
- Implement lazy loading for routes
- Use virtual scrolling for large lists
- Optimize bundle size with tree shaking
- Implement proper caching strategies
- Use Vue DevTools for performance profiling

## Deployment

### Development Deployment
```bash
# Build and start all services
docker compose -f docker-compose.dev.yml up --build

# Scale specific services
docker compose -f docker-compose.dev.yml up --scale app=2
```

### Production Deployment
```bash
# Build production images
docker compose build

# Start production services
docker compose up -d

# Monitor services
docker compose ps
docker compose logs -f
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database status
docker compose ps postgres

# View database logs
docker compose logs postgres

# Connect to database
docker compose exec postgres psql -U kuroibara -d kuroibara
```

#### Frontend Build Issues
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
```

#### Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Fix Docker permissions
sudo usermod -aG docker $USER
```

### Getting Help
- Check the [GitHub Issues](https://github.com/Futs/kuroibara/issues)
- Review the [API Documentation](API_REFERENCE.md)
- Join the community discussions
- Contact the maintainers
