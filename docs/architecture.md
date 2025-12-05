# System Architecture

## Overview

travelers.ai follows a three-tier architecture with clear separation between the mobile client, backend API, and external data sources.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Mobile App    │────▶│   FastAPI       │────▶│   PostgreSQL    │
│   (Expo/RN)     │     │   Backend       │     │   + PostGIS     │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────┴────────┐
                        ▼                 ▼
                 ┌──────────────┐  ┌──────────────┐
                 │    Redis     │  │   External   │
                 │    Cache     │  │   APIs       │
                 └──────────────┘  └──────────────┘
```

## Data Flow

### POI Discovery Pipeline

```
1. User searches for city
   └─▶ City Service searches PostgreSQL
       └─▶ Returns city with coordinates (PostGIS)

2. User selects city
   └─▶ POI Service queries POIs for city_id
       └─▶ Check Redis cache first
       └─▶ Query PostgreSQL if cache miss
       └─▶ Return POI list with pagination

3. User views POI detail
   └─▶ POI Service fetches full POI data
       └─▶ Check Redis cache first
       └─▶ If summary missing and LLM configured:
           └─▶ Fetch Wikipedia extract
           └─▶ Generate AI summary
           └─▶ Store in PostgreSQL
           └─▶ Cache in Redis (30 days)
```

### Data Enrichment Pipeline

```
Wikidata SPARQL ──▶ POI Basic Data ──▶ Wikipedia API ──▶ LLM Provider
       │                  │                   │               │
       ▼                  ▼                   ▼               ▼
    name              coordinates          extract         summary
    inception         architect           article_url      summary_es
    style             image_url
```

## Database Schema

### Core Tables

```
cities
├── id (UUID, PK)
├── name
├── country
├── country_code
├── coordinates (Geography POINT)
├── timezone
├── wikidata_id
├── google_place_id
├── created_at
└── updated_at

pois
├── id (UUID, PK)
├── city_id (FK → cities)
├── name
├── wikidata_id
├── google_place_id
├── wikipedia_url
├── coordinates (Geography POINT)
├── address
├── year_built
├── year_built_circa
├── architect
├── architectural_style
├── heritage_status
├── summary (AI-generated EN)
├── summary_es (AI-generated ES)
├── wikipedia_extract
├── image_url
├── image_attribution
├── poi_type
├── estimated_visit_duration
├── data_quality_score
├── data_source
├── last_verified_at
├── created_at
└── updated_at
```

### Indexes

- `ix_cities_country` - Filter cities by country
- `ix_pois_city_id` - List POIs for a city
- `ix_pois_poi_type` - Filter POIs by type
- `ix_pois_coordinates` (GIST) - Spatial queries

## Caching Strategy

### Redis Cache Keys

| Pattern | TTL | Description |
|---------|-----|-------------|
| `poi:{id}:{lang}` | 30 days | Full POI detail |
| `poi_list:{city_id}:{type}` | 30 days | POI list for city |
| `city:{id}` | 30 days | City detail |
| `city_search:{query}` | 1 day | City search results |

### Cache Invalidation

- POI update → invalidate `poi:{id}:*`
- POI create/delete → invalidate `poi_list:{city_id}:*`
- City update → invalidate `city:{id}` and `city_search:*`

## API Structure

```
/api/v1/
├── /health                    # Health check
├── /cities/
│   ├── /search?q=            # Search cities
│   ├── /nearby?lat=&lng=     # Find nearby cities
│   ├── /by-country/{country} # Cities in country
│   └── /{city_id}            # City detail
├── /pois/
│   ├── ?city_id=             # List POIs
│   ├── /search?q=            # Search POIs
│   ├── /nearby?lat=&lng=     # Nearby POIs
│   ├── /{poi_id}             # POI detail
│   └── /{poi_id}/enrich      # Trigger enrichment
├── /trips/                    # Trip management (planned)
├── /auth/                     # Authentication (planned)
└── /shared/                   # Shared trip viewing (planned)
```

## Mobile Architecture

### State Management

```
Zustand Stores
├── useSettingsStore     # Language, theme preferences
├── useCitiesStore       # City search and selection
├── usePOIsStore         # POI list and detail
└── useTripsStore        # Trip management (planned)
```

### Navigation

```
RootNavigator (Stack)
├── Home              # Landing screen
├── CitySearch        # City search
├── POIList           # POIs for selected city
└── POIDetail         # POI info card
```

## Internationalization

- Supported languages: English (en), Spanish (es)
- Translation keys defined in `@travelers/shared`
- Device language auto-detection with manual override
- AI summaries generated in both languages
