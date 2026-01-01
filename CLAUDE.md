# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

travelers.ai is a travel planning API that provides AI-generated summaries of points of interest (POIs). The API focuses on educational/cultural content rather than booking logistics.

## Project Structure

```
travelers.ai/
├── packages/
│   └── api/          # FastAPI backend (Python 3.11+)
├── docker/           # PostgreSQL + Redis infrastructure
└── models/           # Local LLM models (Qwen3-8B)
```

## Development Commands

### API (packages/api)
```bash
cd packages/api
python -m venv .venv && .venv\Scripts\activate  # Windows
pip install -e ".[dev]"

# Database
PYTHONPATH=src alembic upgrade head           # Run migrations
PYTHONPATH=src python -m travelers_api.scripts.seed  # Seed test data

# Server
PYTHONPATH=src uvicorn travelers_api.main:app --reload --host 0.0.0.0 --port 8000

# Testing
pytest                          # Run all tests
pytest tests/test_pois.py -v    # Run specific test file
pytest -k "test_search"         # Run tests matching pattern

# Linting/Type checking
ruff check src/                 # Lint
ruff check src/ --fix           # Lint with auto-fix
mypy src/                       # Type check
```

### Infrastructure
```bash
docker compose -f docker/docker-compose.yml up -d   # Start PostgreSQL + Redis
```

## Architecture

### Design
- REST API → **FastAPI Backend** → **PostgreSQL + PostGIS** + **Redis Cache**

### Data enrichment pipeline
1. Client requests POI detail
2. Check Redis cache (30-day TTL)
3. If cache miss: query PostgreSQL
4. If summary missing: fetch Wikipedia extract → generate LLM summary → store

### Key modules (packages/api/src/travelers_api/)
- `routers/` - FastAPI route handlers (auth, cities, pois, trips, itineraries, shared, omen)
- `services/` - Business logic (poi_service, city_service, llm)
- `clients/` - External API clients (wikidata, wikipedia, omen)
- `models/` - SQLAlchemy ORM models (city, poi, user, trip, itinerary)
- `core/` - Config, database, cache, security utilities
- `dependencies/` - FastAPI dependency injection (auth)

### LLM Provider System
The `services/llm.py` module implements a provider-agnostic LLM abstraction:
- `LLMProvider` - Abstract base class defining `generate_summary()` interface
- `LlamaCppProvider` - Local inference using llama-cpp-python (runs in thread pool)
- `OpenAIProvider` - OpenAI API (gpt-4o-mini default)
- `AnthropicProvider` - Claude API (claude-3-haiku default)
- `get_llm_provider()` - Factory function that returns configured provider or None

### Omen AI Integration
The `clients/omen.py` module provides WebSocket client for the Omen real-time AI engine:
- `OmenClient` - Manages WebSocket connection with auto-reconnect
- `OmenScreen` - Enum of valid screen types (home, explore, poi_detail, itinerary, etc.)
- `send_context()` - Send navigation context to Omen for proactive insights
- `send_poi_context()` - Convenience method for POI detail pages
- `send_chat()` - Send user messages for AI responses

The `routers/omen.py` exposes this to frontends:
- `GET /omen/status` - Connection status
- `GET /omen/insights` - Current sidebar insights
- `POST /omen/context/poi/{poi_id}` - Auto-send POI context from database
- `POST /omen/chat` - Send chat message (sync response)
- `WebSocket /omen/ws` - Proxy for real-time frontend ↔ Omen communication

See: `C:\Users\juanp\Desktop\code\omen\docs\TRAVELERS_INTEGRATION.md` for full protocol spec.

## API Endpoints

Base: `/api/v1`
- `GET /cities/search?q=` - Search cities
- `GET /cities/{city_id}` - City detail
- `GET /pois?city_id=` - List POIs for city
- `GET /pois/{poi_id}?lang=` - POI detail with AI summary (lang: en|es)
- `POST /auth/register`, `POST /auth/login` - User authentication
- `GET /trips`, `POST /trips` - Trip management (requires auth)
- `GET /health` - Health check

API docs: http://localhost:8000/docs

## Environment Variables

Required variables (no defaults):
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing key (min 32 chars)

Optional variables (see `packages/api/.env.example`):
- `LLM_PROVIDER` - none, llama, openai, anthropic
- `REDIS_URL` - Cache connection (default: redis://localhost:6379)
- `ALLOWED_ORIGINS` - CORS origins (comma-separated)
- `OMEN_ENABLED` - Enable Omen AI integration (default: false)
- `OMEN_WS_URL` - Omen WebSocket URL (default: ws://localhost:8100/ws)

## Database

PostgreSQL 16 with PostGIS extension. Key tables:
- `cities` - City data with coordinates (Geography POINT)
- `pois` - POIs with AI summaries, linked to cities
- `users` - User accounts with hashed passwords
- `trips` / `trip_pois` / `itineraries` - Trip planning

Migrations: `packages/api/alembic/versions/`

## Testing

Tests use SQLite in-memory database and mock settings. Key fixtures in `tests/conftest.py`:
- `client` - AsyncClient with DB override
- `authenticated_client` - Client with auth token
- `sample_user_data`, `sample_city_data`, `sample_poi_data` - Test fixtures
