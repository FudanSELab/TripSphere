# TripSphere Web Frontend

TripSphere's web frontend is built with Nuxt.js, providing a modern, responsive interface for the AI-powered travel assistant platform.

## Features

- 🎨 **Modern UI** - Built with Tailwind CSS with beautiful animations and transitions
- 💬 **AI Chat Interface** - Interactive chat component for the AI travel assistant
- 🏨 **Hotel & Attraction Discovery** - Browse and search hotels and attractions
- 📅 **Itinerary Planning** - AI-powered trip planning with drag-and-drop interface
- 📝 **Travel Notes** - Create and share travel stories with Markdown support
- 🔐 **Authentication** - User login and registration system
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile devices

## Tech Stack

- **Framework**: [Nuxt.js 4](https://nuxt.com) (Vue.js 3)
- **Styling**: [Tailwind CSS](https://tailwindcss.com)
- **Icons**: [Lucide Vue](https://lucide.dev)
- **TypeScript**: Full TypeScript support

## Getting Started

### Prerequisites

- Node.js 18+
- npm or pnpm

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables

Copy `.env.example` to `.env` and configure the backend service URLs:

```bash
cp .env.example .env
```

## Project Structure

```
trip-web-frontend/
├── app/
│   ├── assets/          # CSS and static assets
│   ├── components/      # Vue components
│   │   ├── chat/        # Chat-related components
│   │   ├── layout/      # Layout components (header, footer)
│   │   └── ui/          # Reusable UI components
│   ├── composables/     # Vue composables (hooks)
│   ├── layouts/         # Page layouts
│   ├── pages/           # File-based routing pages
│   ├── types/           # TypeScript type definitions
│   └── utils/           # Utility functions
├── public/              # Static files
├── nuxt.config.ts       # Nuxt configuration
├── tailwind.config.ts   # Tailwind CSS configuration
└── package.json
```

## Pages

- `/` - Home page with hero section and feature overview
- `/chat` - AI chat assistant interface
- `/attractions` - Browse and search attractions
- `/hotels` - Browse and search hotels
- `/itinerary` - AI-powered trip planning
- `/notes` - Travel notes and stories
- `/login` - User login
- `/register` - User registration

## Development

### Code Style

- Use TypeScript for type safety
- Follow Vue 3 Composition API patterns
- Use Tailwind CSS utility classes for styling
- Components use `<script setup lang="ts">` syntax

### Components

UI components are built with a combination of:
- Custom Vue components in `components/ui/`
- Tailwind CSS for styling
- Class Variance Authority (CVA) for component variants

## API Integration

The frontend communicates with backend services via REST APIs. Composables in `app/composables/` provide reactive interfaces for:

- `useChat()` - Chat service integration
- `useAuth()` - Authentication handling

## License

This project is part of the TripSphere platform.
