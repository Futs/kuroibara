# Kuroibara Frontend Application

The Vue.js 3 frontend application for Kuroibara manga management platform.

## Tech Stack

- **Vue.js 3.5.17** - Progressive JavaScript framework with Composition API
- **Vite** - Fast build tool and development server
- **Tailwind CSS 4.0.0** - Utility-first CSS framework
- **Pinia** - State management for Vue.js
- **Vue Router** - Official routing library
- **Headless UI** - Unstyled, accessible UI components
- **TypeScript** - Type-safe JavaScript development

## Features

- **Modern Vue.js Development**: Uses Vue 3 `<script setup>` SFCs and Composition API
- **Type Safety**: Full TypeScript support with type checking
- **Responsive Design**: Mobile-first responsive design with Tailwind CSS
- **Accessibility**: WCAG compliant with screen reader support
- **Performance**: Optimized builds with code splitting and lazy loading
- **Testing**: Comprehensive test suite with Vitest
- **Code Quality**: ESLint, Prettier, and automated formatting

## Development Setup

### Prerequisites

- Node.js 22+
- npm, yarn, or pnpm

### Installation

```bash
# Navigate to the app directory
cd frontend/app

# Install dependencies
npm install
# or
yarn install
# or
pnpm install
```

### Development Server

```bash
# Start development server
npm run dev
# or
yarn dev
# or
pnpm dev
```

The application will be available at `http://localhost:5173`

### Building for Production

```bash
# Build for production
npm run build
# or
yarn build
# or
pnpm build
```

### Testing

```bash
# Run unit tests
npm run test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

### Code Quality

```bash
# Lint and fix code
npm run lint

# Format code with Prettier
npm run format

# Type checking
npm run type-check
```

## Project Structure

```
src/
├── components/          # Reusable Vue components
│   ├── ui/             # Base UI components
│   ├── forms/          # Form components
│   └── layout/         # Layout components
├── views/              # Page components
├── stores/             # Pinia stores
├── router/             # Vue Router configuration
├── utils/              # Utility functions
├── composables/        # Vue composables
├── types/              # TypeScript type definitions
├── assets/             # Static assets
└── style.css           # Global styles
```

## Key Technologies

### Vue.js 3 with Composition API

The application uses Vue 3's Composition API with `<script setup>` syntax for better TypeScript integration and improved developer experience.

### Tailwind CSS 4.0

Utility-first CSS framework for rapid UI development with:
- Responsive design utilities
- Dark mode support
- Custom component styling
- Optimized production builds

### Pinia State Management

Modern state management with:
- Intuitive API design
- TypeScript support
- DevTools integration
- Modular store architecture

### Vite Build Tool

Fast development and optimized production builds with:
- Hot module replacement (HMR)
- Optimized bundling
- Plugin ecosystem
- TypeScript support

## IDE Support

For the best development experience, use:

- **VS Code** with Vue Language Features (Volar) extension
- **WebStorm** with Vue.js plugin
- **Vim/Neovim** with appropriate Vue.js plugins

Learn more about IDE Support for Vue in the [Vue Docs Scaling up Guide](https://vuejs.org/guide/scaling-up/tooling.html#ide-support).

## Contributing

1. Follow the established code style and formatting
2. Write tests for new features
3. Ensure TypeScript types are properly defined
4. Update documentation as needed

## Resources

- [Vue.js 3 Documentation](https://vuejs.org/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [Pinia Documentation](https://pinia.vuejs.org/)
- [Vue Router Documentation](https://router.vuejs.org/)
