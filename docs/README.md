# travelers.ai Documentation

A mobile-first travel planning application that helps users discover and explore points of interest with AI-generated summaries.

## Architecture Overview

```
travelers.ai/
├── packages/
│   ├── api/          # FastAPI backend (Python)
│   ├── mobile/       # React Native/Expo app (TypeScript)
│   └── shared/       # Shared types and utilities (TypeScript)
└── docs/             # Documentation
```

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker (for PostgreSQL + Redis)
- pnpm

### Development Setup

```bash
# Install dependencies
pnpm install

# Start infrastructure
docker-compose up -d

# Run database migrations
cd packages/api
source .venv/bin/activate
PYTHONPATH=src alembic upgrade head

# Seed test data
PYTHONPATH=src python -m travelers_api.scripts.seed

# Start API server
PYTHONPATH=src uvicorn travelers_api.main:app --port 8000

# Start mobile app (in another terminal)
cd packages/mobile
pnpm start
```

## Documentation Index

- [Architecture](./architecture.md) - System design and data flow
- [API Documentation](./api/README.md) - Backend services and endpoints
- [Mobile App](./mobile/README.md) - React Native app structure
- [Shared Package](./shared/README.md) - Types and utilities

## Key Features

1. **City Search** - Find cities worldwide with autocomplete
2. **POI Discovery** - Browse points of interest with rich metadata
3. **AI Info Cards** - AI-generated summaries in English and Spanish
4. **Offline Support** - Local caching for offline access (planned)
5. **Trip Planning** - Create and manage trips with POIs (planned)

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, SQLAlchemy 2.0, PostgreSQL + PostGIS |
| Caching | Redis with 30-day TTL |
| Mobile | React Native, Expo, Zustand |
| Data Sources | Wikidata SPARQL, Wikipedia API |
| AI | Provider-agnostic LLM integration |
