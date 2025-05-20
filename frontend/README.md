# Kurobara Frontend

The frontend for the Kurobara manga/manhua/manhwa library application.

## Features

- User authentication with 2FA
- Manga search across multiple providers
- Library management
- Reading progress tracking
- Bookmarks
- Categories and reading lists
- Download management
- Manga reader

## Tech Stack

- Vue.js
- Tailwind CSS

## Development

### Prerequisites

- Node.js
- npm or yarn

### Setup

1. Clone the repository
2. Install dependencies: `npm install` or `yarn install`
3. Start the development server: `npm run dev` or `yarn dev`

## Project Structure

```
frontend/
├── app/                      # Application code
│   ├── assets/               # Static assets
│   ├── components/           # Vue components
│   ├── pages/                # Vue pages
│   ├── router/               # Vue Router
│   ├── store/                # Vuex store
│   ├── utils/                # Utility functions
│   └── App.vue               # Root component
└── Dockerfile                # Docker configuration
```

## Building for Production

```bash
npm run build
# or
yarn build
```
