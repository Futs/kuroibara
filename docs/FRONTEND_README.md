# Kuroibara Frontend

The frontend for the Kuroibara manga/manhua/manhwa library application.

## Features

- User authentication with 2FA support
- Manga search across 80+ providers with advanced filtering
- Smart library management with categories and reading lists
- Advanced reading progress tracking and analytics
- Page-level bookmarks with notes
- Advanced manga reader with multiple viewing modes
- Download management with background processing
- Customizable UI themes and layouts
- Reading statistics and achievement system

## Tech Stack

- Vue.js 3.5.17 with Composition API
- Tailwind CSS 4.0.0
- Vite for build tooling
- Pinia for state management
- Vue Router for navigation
- Headless UI for accessible components
- TypeScript support

## Development

### Prerequisites

- Node.js 22+
- npm or yarn or pnpm

### Setup

1. Clone the repository
2. Navigate to frontend directory: `cd frontend/app`
3. Install dependencies: `npm install` or `yarn install` or `pnpm install`
4. Start the development server: `npm run dev` or `yarn dev` or `pnpm dev`

### Quick Start with Docker

```bash
# Using Docker Compose (recommended)
docker compose up -d

# Access the application at http://localhost:3000
```

## Project Structure

```
frontend/
├── app/                      # Vue.js application
│   ├── src/                  # Source code
│   │   ├── components/       # Vue components
│   │   ├── views/            # Vue pages/views
│   │   ├── router/           # Vue Router configuration
│   │   ├── stores/           # Pinia stores
│   │   ├── utils/            # Utility functions
│   │   └── App.vue           # Root component
│   ├── public/               # Static assets
│   ├── package.json          # Dependencies
│   └── vite.config.js        # Vite configuration
├── Dockerfile                # Docker configuration
└── nginx.conf                # Nginx configuration
```

## Building for Production

```bash
npm run build
# or
yarn build
# or
pnpm build
```

## Testing

```bash
# Run unit tests
npm run test
# or
yarn test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

## Code Quality

```bash
# Lint code
npm run lint

# Format code
npm run format

# Type checking
npm run type-check
```
