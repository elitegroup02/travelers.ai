# API Documentation

The travelers.ai API is built with FastAPI and provides endpoints for cities, POIs, and trip management.

## Base URL

- Development: `http://localhost:8000/api/v1`
- API Documentation: `http://localhost:8000/docs` (Swagger UI)

## Directory Structure

```
packages/api/src/travelers_api/
├── main.py                 # FastAPI application entry
├── core/
│   ├── config.py          # Settings from environment
│   ├── database.py        # SQLAlchemy async session
│   └── cache.py           # Redis caching layer
├── models/
│   ├── city.py            # City model with PostGIS
│   ├── poi.py             # POI model
│   ├── trip.py            # Trip model
│   ├── itinerary.py       # Itinerary model
│   └── user.py            # User model
├── routers/
│   ├── health.py          # Health check endpoint
│   ├── cities.py          # City endpoints
│   ├── pois.py            # POI endpoints
│   ├── trips.py           # Trip endpoints (stub)
│   ├── itineraries.py     # Itinerary endpoints (stub)
│   └── auth.py            # Auth endpoints (stub)
├── services/
│   ├── city_service.py    # City operations
│   ├── poi_service.py     # POI operations with enrichment
│   └── llm.py             # LLM provider abstraction
├── clients/
│   ├── wikidata.py        # Wikidata SPARQL client
│   └── wikipedia.py       # Wikipedia API client
└── scripts/
    └── seed.py            # Database seeding
```

## Endpoints

### Cities

#### `GET /cities/search`

Search cities by name.

**Parameters:**
- `q` (required): Search query (min 2 chars)
- `limit` (optional): Max results (1-50, default 10)

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Barcelona",
      "country": "Spain",
      "country_code": "ES",
      "coordinates": { "lat": 41.3851, "lng": 2.1734 },
      "timezone": "Europe/Madrid",
      "wikidata_id": "Q1492"
    }
  ],
  "total": 1
}
```

#### `GET /cities/{city_id}`

Get city by ID.

#### `GET /cities/nearby`

Find cities near coordinates.

**Parameters:**
- `lat`, `lng` (required): Coordinates
- `radius_km` (optional): Search radius (1-500, default 100)
- `limit` (optional): Max results (1-50, default 10)

### POIs

#### `GET /pois`

List POIs for a city.

**Parameters:**
- `city_id` (required): City UUID
- `poi_type` (optional): Filter by type
- `limit` (optional): Max results (1-100, default 20)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "La Sagrada Familia",
      "coordinates": { "lat": 41.4036, "lng": 2.1744 },
      "poi_type": "church",
      "year_built": 1882,
      "image_url": "https://...",
      "estimated_visit_duration": 90
    }
  ],
  "total": 7,
  "has_more": false
}
```

#### `GET /pois/{poi_id}`

Get POI detail with AI summary.

**Parameters:**
- `lang` (optional): Summary language ("en" | "es", default "en")

**Response:**
```json
{
  "id": "uuid",
  "name": "La Sagrada Familia",
  "city_id": "uuid",
  "coordinates": { "lat": 41.4036, "lng": 2.1744 },
  "poi_type": "church",
  "year_built": 1882,
  "architect": "Antoni Gaudí",
  "architectural_style": "Modernisme",
  "heritage_status": "UNESCO World Heritage Site",
  "summary": "Construction began in 1882...",
  "wikipedia_url": "https://en.wikipedia.org/wiki/...",
  "image_url": "https://...",
  "estimated_visit_duration": 90
}
```

#### `GET /pois/search`

Search POIs by name.

#### `GET /pois/nearby`

Find POIs near coordinates.

#### `POST /pois/{poi_id}/enrich`

Manually trigger data enrichment (Wikipedia + AI summary).

## Services

### CityService

Handles city operations with PostGIS spatial queries.

**Key methods:**
- `search_cities(query, limit)` - Text search with caching
- `get_city(city_id)` - Get by ID with caching
- `find_nearby_cities(lat, lng, radius_km)` - Spatial search

### POIService

Handles POI operations with the full data enrichment pipeline.

**Key methods:**
- `get_pois_for_city(city_id, poi_type, limit, offset)` - List with pagination
- `get_poi(poi_id, language, generate_summary)` - Detail with on-demand summary
- `search_pois(query, city_id)` - Text search
- `get_nearby_pois(lat, lng, radius_meters)` - Spatial search
- `enrich_poi(poi_id)` - Fetch Wikipedia + generate AI summaries

### LLM Provider

Provider-agnostic interface for AI summary generation.

Supported providers (via environment):
- `ANTHROPIC_API_KEY` - Claude models
- `OPENAI_API_KEY` - GPT models

## External Clients

### WikidataClient

Queries Wikidata SPARQL endpoint for POI metadata.

**Methods:**
- `get_poi_by_name(poi_name, city_name)` - Find POI by name
- `get_tourist_attractions_in_city(wikidata_id, limit)` - List attractions

### WikipediaClient

Fetches article extracts and performs geosearch.

**Methods:**
- `get_article_extract(title, language, sentences)` - Get intro extract
- `search_nearby_landmarks(lat, lng, radius, limit)` - Geosearch
- `get_article_url(title, language)` - Build article URL

## Configuration

Environment variables (see `.env.example`):

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/travelers
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=sk-ant-...  # Optional
OPENAI_API_KEY=sk-...         # Optional
```
