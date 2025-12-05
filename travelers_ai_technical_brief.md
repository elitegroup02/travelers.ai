# travelers.ai - Technical Research & Implementation Brief

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision & Core Features](#2-product-vision--core-features)
3. [Competitive Analysis](#3-competitive-analysis)
4. [Data Sources & APIs](#4-data-sources--apis)
5. [Technical Architecture](#5-technical-architecture)
6. [Data Pipeline Specification](#6-data-pipeline-specification)
7. [Database Schema](#7-database-schema)
8. [API Endpoints Design](#8-api-endpoints-design)
9. [Cost Analysis](#9-cost-analysis)
10. [Implementation Roadmap](#10-implementation-roadmap)
11. [Risk Assessment](#11-risk-assessment)
12. [Appendix: Code Examples](#appendix-code-examples)

---

## 1. Executive Summary

### 1.1 Product Concept

**travelers.ai** is a mobile-first travel planning application that differentiates itself by providing concise, educational content about points of interest (POIs). Unlike existing apps that focus on "where to go," travelers.ai answers "what will I see and why does it matter."

### 1.2 Key Differentiator

The core innovation is the **POI Info Card**: a 3-line summary containing:
- Year of construction/founding
- Architect/creator (when applicable)  
- 3 key characteristics or historical facts

**Example Output:**
```
Granada Cathedral
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Built: 1523 | Architect: Diego de Siloé | Style: Spanish Renaissance

Built over a former mosque after the Reconquista, this 16th-century 
cathedral showcases Diego de Siloé's masterful Renaissance design. 
Look up at the massive dome—it was revolutionary for its time. The 
Royal Chapel next door houses Ferdinand and Isabella's tombs.
```

### 1.3 Target Users

- Cultural/educational travelers (not backpackers or luxury travelers)
- Students on exchange programs in Europe
- Spanish-speaking tourists visiting Spain (initial market)
- Teachers and educational groups

### 1.4 Core User Flow

1. User knows destination + travel dates + POIs they want to visit
2. User searches city → sees POIs on map
3. User taps POI → sees info card with historical/cultural data
4. User adds POIs to trip → app generates logical daily itinerary
5. User exports/shares itinerary

### 1.5 Market Gap

**No existing app combines:**
- Trip planning functionality
- Educational/cultural content about POIs
- Concise, LLM-generated summaries
- Mobile-first experience

Existing apps (Layla, Mindtrip, TripIt, Wanderlog) focus on logistics (flights, hotels, bookings) but provide zero historical/cultural context about attractions.

---

## 2. Product Vision & Core Features

### 2.1 MVP Features (Phase 1)

| Feature | Description | Priority |
|---------|-------------|----------|
| City Search | Search for destinations, display on map | P0 |
| POI Discovery | Show top POIs in selected city | P0 |
| Info Cards | Year, architect, 3-line summary for each POI | P0 |
| Trip Builder | Add POIs to "My Trip" with date selection | P0 |
| Itinerary Generator | Create daily schedule with travel times | P0 |
| Export/Share | Share itinerary as link or export to PDF | P0 |

### 2.2 Phase 2 Features

| Feature | Description | Priority |
|---------|-------------|----------|
| User Accounts | Persist trips across devices | P1 |
| Affiliate Links | Booking.com, Viator, GetYourGuide integration | P1 |
| Multiple Trips | Save and manage multiple trips | P1 |
| Collaborative Planning | Share trip with others for co-editing | P1 |

### 2.3 Phase 3 Features

| Feature | Description | Priority |
|---------|-------------|----------|
| Smart Suggestions | Recommend POIs based on user profile | P2 |
| Offline Mode | Download city data for offline access | P2 |
| Audio Guides | LLM-generated audio descriptions | P2 |
| User Reviews/Tips | Community-contributed insights | P2 |

### 2.4 Explicitly Out of Scope (MVP)

- Flight booking
- Hotel booking
- Restaurant reservations
- Social features beyond sharing
- Real-time opening hours (link out instead)
- Ticket purchasing

---

## 3. Competitive Analysis

### 3.1 Direct Competitors

#### Tier 1: Well-Funded AI Trip Planners

| App | Funding | Model | Strengths | Weaknesses |
|-----|---------|-------|-----------|------------|
| **Layla.ai** | Undisclosed | Booking commissions (Booking.com, Skyscanner, GetYourGuide) | End-to-end booking, 1.1M+ trips, 4.9★ rating | No cultural/historical POI info |
| **Mindtrip** | $19M | Booking + DMO partnerships + Creator program | Import from YouTube/TikTok, collaborative planning | More "mood board" than executable planner |
| **TripIt** | Acquired by SAP Concur | $49/year Pro subscription | Auto-import from emails, excellent for business travelers | No recommendations, no cultural info |
| **Wanderlog** | Bootstrapped | $39.99/year Pro, generous freemium | Group collaboration, budget tracking, great maps | Manual entry required, no historical POI data |

#### Tier 2: Emerging AI Planners

| App | Price | Differentiator |
|-----|-------|----------------|
| Wonderplan | Free (for now) | Personalized itineraries, PDF export |
| iplan.ai | ~$4-6 one-time | Minute-by-minute route planning |
| GuideGeek | Free (WhatsApp-based) | No app download, 7M+ questions answered |
| Vacay | Freemium | Thematic advisors (romance, adventure, etc.) |

### 3.2 Competitive Gap Analysis

**What NO competitor does well:**
1. Concise historical/cultural info about POIs
2. Education-focused travel planning
3. "Travel Wikipedia" integrated into planning flow
4. Targeting cultural/educational travelers specifically

### 3.3 Monetization Models in Use

| Model | Who Uses It | Potential Revenue |
|-------|-------------|-------------------|
| **Affiliate bookings** | Layla, Mindtrip, Wanderlog | 5-15% commission per booking |
| **Freemium/Subscription** | TripIt ($49/yr), Wanderlog ($40/yr), Roadtrippers ($36/yr) | $3-7/month/user |
| **Creator programs** | Mindtrip | Up to $10K/month to content creators |
| **DMO Partnerships** | Mindtrip | B2B contracts with tourism boards |

### 3.4 Monetization Options

**MVP:** Free with daily search limits

**Post-MVP options:**
- Freemium: Basic free, Pro with offline + advanced features
- Affiliate links: Viator, GetYourGuide for tours/experiences
- Sponsored POIs: Museums/attractions pay for featured placement

---

## 4. Data Sources & APIs

### 4.1 Data Source Overview

| Source | Data Provided | Cost | Quality |
|--------|---------------|------|---------|
| **Wikidata SPARQL** | Coordinates, inception dates, architects, styles, heritage status | FREE | High for famous POIs |
| **Wikipedia API** | Article extracts, geosearch for landmarks | FREE | High |
| **DBpedia** | Structured Wikipedia data via SPARQL | FREE | Medium-High |
| **Wikimedia Monuments DB** | 1.6M+ cultural heritage monuments | FREE | High for heritage sites |
| **Google Places API** | POI identification, coordinates, hours, photos | $2-30 per 1K requests | Excellent |
| **OpenStreetMap** | POI coordinates, basic metadata | FREE | Good |
| **Foursquare Places** | 105M POIs, tips, photos | Freemium | Good |
| **TripAdvisor Content API** | Reviews, ratings (partners only) | Partnership required | Excellent |

### 4.2 Wikidata SPARQL Queries

#### 4.2.1 Get POI Basic Info

```sparql
# Query: Get basic info for a landmark
SELECT ?item ?itemLabel ?inception ?architectLabel ?styleLabel ?image ?coords WHERE {
  ?item rdfs:label "Granada Cathedral"@en .
  OPTIONAL { ?item wdt:P571 ?inception }      # inception date
  OPTIONAL { ?item wdt:P84 ?architect }        # architect
  OPTIONAL { ?item wdt:P149 ?style }           # architectural style
  OPTIONAL { ?item wdt:P18 ?image }            # image from Wikimedia Commons
  OPTIONAL { ?item wdt:P625 ?coords }          # coordinates
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

#### 4.2.2 Get Tourist Attractions in a City

```sparql
# Query: Get tourist attractions in Granada, Spain
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

SELECT DISTINCT ?attraction ?attractionLabel ?coords ?inception WHERE {
  ?attraction (wdt:P31/wdt:P279*) wd:Q570116 .  # instance of tourist attraction
  ?attraction wdt:P131 wd:Q8810 .                # located in Granada
  OPTIONAL { ?attraction wdt:P625 ?coords }
  OPTIONAL { ?attraction wdt:P571 ?inception }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 100
```

#### 4.2.3 Wikidata Property Reference

| Property | Code | Description |
|----------|------|-------------|
| Instance of | P31 | What type of thing (cathedral, museum, etc.) |
| Located in | P131 | Administrative territory |
| Inception | P571 | Date founded/built |
| Architect | P84 | Person who designed |
| Architectural style | P149 | Gothic, Renaissance, etc. |
| Coordinates | P625 | Latitude/longitude |
| Image | P18 | Wikimedia Commons image |
| Heritage designation | P1435 | UNESCO, national heritage, etc. |
| Country | P17 | Country location |

### 4.3 Wikipedia API Usage

#### 4.3.1 Get Article Extract

```
GET https://en.wikipedia.org/w/api.php?
    action=query&
    titles=Granada_Cathedral&
    prop=extracts&
    exintro=true&
    explaintext=true&
    format=json
```

#### 4.3.2 Geosearch for Landmarks

```
GET https://en.wikipedia.org/w/api.php?
    action=query&
    list=geosearch&
    gsradius=10000&
    gscoord=37.1761|-3.5986&
    gslimit=50&
    gsprop=type|name&
    format=json
```

### 4.4 Google Places API Usage

#### 4.4.1 Text Search for POIs

```
POST https://places.googleapis.com/v1/places:searchText
Headers:
  X-Goog-Api-Key: YOUR_API_KEY
  X-Goog-FieldMask: places.id,places.displayName,places.formattedAddress,places.location

Body:
{
  "textQuery": "tourist attractions in Granada Spain"
}
```

#### 4.4.2 Place Details

```
GET https://places.googleapis.com/v1/places/{PLACE_ID}
Headers:
  X-Goog-Api-Key: YOUR_API_KEY
  X-Goog-FieldMask: displayName,formattedAddress,location,rating,regularOpeningHours,photos
```

#### 4.4.3 Google Places API Pricing

| SKU | Cost per 1,000 requests |
|-----|------------------------|
| Text Search (Basic) | $32.00 |
| Place Details (Basic) | $17.00 |
| Place Details (Contact) | $20.00 |
| Place Details (Atmosphere) | $25.00 |
| Autocomplete (per session) | $2.83 |

**Note:** Use FieldMask to request only needed fields and reduce costs. Check current Google pricing for free tier details.

### 4.5 Data Coverage Analysis

| POI Type | Wikidata Coverage | Data Completeness |
|----------|-------------------|-------------------|
| UNESCO World Heritage Sites | ~95% | High |
| Major landmarks (top 100/country) | ~90% | Medium-High |
| Regional attractions | ~70% | Medium |
| Local/obscure POIs | ~40% | Low |

**Note:** MVP should focus on well-known POIs where data quality is high. Implement graceful fallback for data gaps.

---

## 5. Technical Architecture

### 5.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                 │
│                                                                      │
│  ┌─────────────────────┐    ┌─────────────────────┐                │
│  │   iOS App           │    │   Android App       │                │
│  │   (React Native     │    │   (React Native     │                │
│  │    via Expo)        │    │    via Expo)        │                │
│  └─────────────────────┘    └─────────────────────┘                │
│                                                                      │
│  ┌─────────────────────────────────────────────────┐                │
│  │              Web App (Optional Phase 2)          │                │
│  │              Next.js / React                     │                │
│  └─────────────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTPS / REST API
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API LAYER                                    │
│                                                                      │
│  ┌─────────────────────────────────────────────────┐                │
│  │              FastAPI Backend (Python)            │                │
│  │                                                  │                │
│  │  • /api/v1/cities                               │                │
│  │  • /api/v1/pois                                 │                │
│  │  • /api/v1/trips                                │                │
│  │  • /api/v1/itineraries                          │                │
│  └─────────────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│   POI Service     │ │  Route Service    │ │  User Service     │
│                   │ │                   │ │                   │
│ • Wikidata client │ │ • Travel time     │ │ • Auth (Phase 2)  │
│ • Wikipedia client│ │   calculation     │ │ • Trip storage    │
│ • Google Places   │ │ • Itinerary       │ │ • Preferences     │
│ • LLM summarizer  │ │   optimization    │ │                   │
└───────────────────┘ └───────────────────┘ └───────────────────┘
                │               │               │
                └───────────────┼───────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                   │
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │   PostgreSQL    │  │     Redis       │  │   S3 / R2       │     │
│  │                 │  │                 │  │                 │     │
│  │ • POI data      │  │ • API cache     │  │ • Images        │     │
│  │ • Users         │  │ • Sessions      │  │ • Exports       │     │
│  │ • Trips         │  │ • Rate limits   │  │ • Static assets │     │
│  │ • Itineraries   │  │                 │  │                 │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                               │
│                                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Wikidata │ │Wikipedia │ │ Google   │ │ OpenAI / │ │ Mapbox / │ │
│  │ SPARQL   │ │ API      │ │ Places   │ │ Anthropic│ │ Google   │ │
│  │          │ │          │ │ API      │ │ API      │ │ Maps     │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Technology Stack

#### 5.2.1 Mobile (Primary)

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Framework | React Native (Expo) | Single codebase iOS/Android, familiar React paradigm |
| Navigation | React Navigation | Industry standard for RN |
| State | Zustand or Redux Toolkit | Lightweight, performant |
| Maps | react-native-maps | Native performance, supports both Google and Apple Maps |
| HTTP Client | Axios or fetch | Standard |
| Storage | AsyncStorage + SecureStore | Device-local persistence |

#### 5.2.2 Backend

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Framework | FastAPI (Python) | Async, fast, excellent for LLM integrations |
| Validation | Pydantic | Built into FastAPI, type safety |
| ORM | SQLAlchemy 2.0 | Async support, mature ecosystem |
| Migrations | Alembic | Standard for SQLAlchemy |
| Task Queue | Celery + Redis (if needed) | Background processing |
| Testing | pytest + httpx | Async testing support |

#### 5.2.3 Infrastructure

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Database | PostgreSQL 15+ | PostGIS for geo queries, JSON support |
| Cache | Redis | Session storage, API caching |
| Object Storage | Cloudflare R2 or AWS S3 | Image storage, exports |
| Hosting | Railway / Render / Fly.io | Easy deployment, reasonable pricing |
| CDN | Cloudflare | Global distribution |

#### 5.2.4 External APIs

| Service | Purpose | Estimated Cost |
|---------|---------|----------------|
| Google Places API | POI identification, coordinates | Pay per use (~$17-32/1K requests) |
| Wikidata SPARQL | Historical data | FREE |
| Wikipedia API | Article extracts | FREE |
| OpenAI GPT-4o-mini | Summary generation | ~$0.15-0.60/1M tokens |
| Mapbox OR Google Maps SDK | Map display in app | Free tier generous |
| OpenRouteService (optional) | Directions/routing | FREE alternative to Google |

### 5.3 Mobile App Structure

```
/src
├── /api
│   ├── client.ts           # Axios instance, interceptors
│   ├── pois.ts             # POI endpoints
│   ├── trips.ts            # Trip endpoints
│   └── itineraries.ts      # Itinerary endpoints
├── /components
│   ├── /common
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   └── Loading.tsx
│   ├── /poi
│   │   ├── POICard.tsx     # The info card component
│   │   ├── POIList.tsx
│   │   └── POIMap.tsx
│   ├── /trip
│   │   ├── TripBuilder.tsx
│   │   ├── TripItem.tsx
│   │   └── DatePicker.tsx
│   └── /itinerary
│       ├── ItineraryView.tsx
│       ├── DaySection.tsx
│       └── TimeSlot.tsx
├── /screens
│   ├── HomeScreen.tsx
│   ├── SearchScreen.tsx
│   ├── POIDetailScreen.tsx
│   ├── TripScreen.tsx
│   ├── ItineraryScreen.tsx
│   └── SettingsScreen.tsx
├── /store
│   ├── index.ts            # Zustand store setup
│   ├── tripStore.ts
│   └── settingsStore.ts
├── /hooks
│   ├── usePOIs.ts
│   ├── useTrip.ts
│   └── useLocation.ts
├── /utils
│   ├── formatting.ts
│   ├── geo.ts
│   └── storage.ts
├── /types
│   └── index.ts            # TypeScript interfaces
└── App.tsx
```

---

## 6. Data Pipeline Specification

### 6.1 POI Data Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│ INPUT: POI name + city (e.g., "Granada Cathedral, Granada, Spain")  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: Check Cache                                                  │
│                                                                      │
│ • Query Redis/PostgreSQL for existing POI data                      │
│ • If found and fresh (< 30 days): return cached data                │
│ • If not found or stale: continue to Step 2                         │
│                                                                      │
│ Cost: $0 (local operation)                                          │
└─────────────────────────────────────────────────────────────────────┘
                                │ Cache miss
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: Identify & Disambiguate                                      │
│                                                                      │
│ Option A: Google Places API                                         │
│   POST /places:searchText { "textQuery": "Granada Cathedral Spain" }│
│   → Returns: place_id, coordinates, name                            │
│   Cost: ~$0.032 per request                                         │
│                                                                      │
│ Option B: Wikidata Search (free alternative)                        │
│   Query for item with label matching POI name in city               │
│   → Returns: Q-number (e.g., Q756687)                               │
│   Cost: $0                                                          │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: Fetch Structured Data (Wikidata)                            │
│                                                                      │
│ SPARQL Query:                                                        │
│ SELECT ?inception ?architectLabel ?styleLabel ?image ?heritageLabel │
│ WHERE {                                                              │
│   wd:Q756687 wdt:P571 ?inception .                                  │
│   OPTIONAL { wd:Q756687 wdt:P84 ?architect }                        │
│   OPTIONAL { wd:Q756687 wdt:P149 ?style }                           │
│   OPTIONAL { wd:Q756687 wdt:P18 ?image }                            │
│   OPTIONAL { wd:Q756687 wdt:P1435 ?heritage }                       │
│   SERVICE wikibase:label { bd:serviceParam wikibase:language "en" } │
│ }                                                                    │
│                                                                      │
│ → Returns: { inception: "1523", architect: "Diego de Siloé", ... }  │
│ Cost: $0                                                            │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: Fetch Wikipedia Extract                                      │
│                                                                      │
│ GET wikipedia.org/w/api.php?action=query&prop=extracts&exintro=true │
│     &titles=Granada_Cathedral&explaintext=true&format=json          │
│                                                                      │
│ → Returns: First paragraph of Wikipedia article (plain text)         │
│ Cost: $0                                                            │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 5: LLM Summarization                                            │
│                                                                      │
│ Model: GPT-4o-mini (or Claude 3.5 Haiku)                            │
│                                                                      │
│ PROMPT:                                                              │
│ """                                                                  │
│ You are a travel guide writer. Given this data about a POI:         │
│                                                                      │
│ Name: {poi_name}                                                     │
│ Built: {inception_year}                                              │
│ Architect: {architect}                                               │
│ Style: {style}                                                       │
│ Wikipedia Extract: {extract}                                         │
│                                                                      │
│ Generate a 3-sentence summary (max 60 words total) that a tourist   │
│ would find useful and memorable. Include:                            │
│ 1. One historical context fact                                       │
│ 2. One visual/architectural highlight to look for                    │
│ 3. One practical tip or lesser-known fact                            │
│                                                                      │
│ Write in an engaging, conversational tone. Do not use generic       │
│ phrases like "must-see" or "don't miss."                            │
│ """                                                                  │
│                                                                      │
│ → Returns: 3-sentence summary                                        │
│ Cost: ~$0.0003 per POI (~500 tokens)                                │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 6: Store & Return                                               │
│                                                                      │
│ • Store complete POI data in PostgreSQL                             │
│ • Cache in Redis with 30-day TTL                                    │
│ • Return JSON response to client                                     │
│                                                                      │
│ Cost: $0 (storage negligible)                                       │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ OUTPUT:                                                              │
│ {                                                                    │
│   "id": "poi_abc123",                                               │
│   "name": "Granada Cathedral",                                       │
│   "coordinates": { "lat": 37.1761, "lng": -3.5986 },                │
│   "year_built": 1523,                                                │
│   "architect": "Diego de Siloé",                                     │
│   "style": "Spanish Renaissance",                                    │
│   "summary": "Built over a former mosque after the Reconquista...", │
│   "image_url": "https://commons.wikimedia.org/...",                 │
│   "wikipedia_url": "https://en.wikipedia.org/wiki/Granada_Cathedral"│
│   "heritage_status": "UNESCO World Heritage Site",                   │
│   "estimated_visit_duration": 60,  // minutes                        │
│   "data_quality_score": 0.95                                         │
│ }                                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Itinerary Generation Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│ INPUT:                                                               │
│ {                                                                    │
│   "date": "2025-03-15",                                             │
│   "start_time": "09:00",                                            │
│   "end_time": "18:00",                                              │
│   "pois": ["poi_abc123", "poi_def456", "poi_ghi789"],               │
│   "start_location": { "lat": 37.1773, "lng": -3.5986 }  // hotel    │
│ }                                                                    │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: Fetch POI Data                                               │
│                                                                      │
│ • Retrieve full POI objects from cache/database                     │
│ • Include coordinates, estimated_visit_duration                      │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: Calculate Travel Times                                       │
│                                                                      │
│ Build distance matrix between all POIs                               │
│                                                                      │
│ Option A: Google Directions API                                      │
│   Cost: ~$5 per 1000 elements                                       │
│                                                                      │
│ Option B: OpenRouteService (free)                                    │
│   POST /v2/matrix/driving-car                                        │
│   Body: { "locations": [[lng,lat], [lng,lat], ...] }                │
│                                                                      │
│ → Returns: Matrix of travel times in seconds                        │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: Optimize Route (Optional - can use simple greedy)           │
│                                                                      │
│ Algorithm: Nearest Neighbor (simple) or 2-opt (better)              │
│                                                                      │
│ def optimize_route(pois, distance_matrix):                          │
│     # Start with nearest neighbor                                    │
│     route = [start_location]                                         │
│     remaining = set(pois)                                            │
│     while remaining:                                                 │
│         nearest = min(remaining, key=lambda p: dist(route[-1], p))  │
│         route.append(nearest)                                        │
│         remaining.remove(nearest)                                    │
│     return route                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: Build Schedule                                               │
│                                                                      │
│ def build_schedule(route, start_time, travel_times):                │
│     schedule = []                                                    │
│     current_time = start_time                                        │
│                                                                      │
│     for i, poi in enumerate(route):                                 │
│         # Add travel time                                            │
│         if i > 0:                                                    │
│             travel_min = travel_times[i-1][i] / 60                  │
│             current_time += travel_min                               │
│                                                                      │
│         schedule.append({                                            │
│             "poi": poi,                                              │
│             "arrival": current_time,                                 │
│             "departure": current_time + poi.visit_duration,         │
│             "travel_from_previous": travel_min if i > 0 else 0      │
│         })                                                           │
│                                                                      │
│         current_time += poi.visit_duration                          │
│                                                                      │
│     return schedule                                                  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ OUTPUT:                                                              │
│ {                                                                    │
│   "date": "2025-03-15",                                             │
│   "total_duration_hours": 7.5,                                      │
│   "total_walking_minutes": 45,                                      │
│   "schedule": [                                                      │
│     {                                                                │
│       "poi": { ... full POI object ... },                           │
│       "arrival": "09:00",                                           │
│       "departure": "10:00",                                         │
│       "travel_from_previous_minutes": 0                             │
│     },                                                               │
│     {                                                                │
│       "poi": { ... },                                               │
│       "arrival": "10:15",                                           │
│       "departure": "12:15",                                         │
│       "travel_from_previous_minutes": 15                            │
│     },                                                               │
│     ...                                                              │
│   ]                                                                  │
│ }                                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.3 Data Quality Handling

```python
def calculate_data_quality_score(poi_data: dict) -> float:
    """
    Calculate a 0-1 score indicating completeness of POI data.
    Used to inform users and prioritize data enrichment.
    """
    score = 0.0
    weights = {
        "name": 0.15,
        "coordinates": 0.20,
        "year_built": 0.15,
        "architect": 0.10,
        "style": 0.10,
        "summary": 0.15,
        "image_url": 0.10,
        "wikipedia_url": 0.05
    }
    
    for field, weight in weights.items():
        if poi_data.get(field):
            score += weight
    
    return round(score, 2)


def get_fallback_summary(poi_name: str, poi_type: str) -> str:
    """
    Generate a basic fallback when full data is unavailable.
    """
    fallbacks = {
        "church": f"{poi_name} is a historic church. Check local sources for visiting hours and history.",
        "museum": f"{poi_name} houses collections worth exploring. Visit their official website for current exhibitions.",
        "monument": f"{poi_name} is a notable landmark. Consider hiring a local guide for deeper insights.",
        "default": f"{poi_name} is a point of interest in this area. Research online for the latest visitor information."
    }
    return fallbacks.get(poi_type, fallbacks["default"])
```

---

## 7. Database Schema

### 7.1 PostgreSQL Schema

```sql
-- Enable PostGIS for geographic queries
CREATE EXTENSION IF NOT EXISTS postgis;

-- Cities table (for caching city data)
CREATE TABLE cities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL,
    country_code CHAR(2),
    coordinates GEOGRAPHY(POINT, 4326) NOT NULL,
    timezone VARCHAR(50),
    wikidata_id VARCHAR(20),
    google_place_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(name, country)
);

CREATE INDEX idx_cities_coordinates ON cities USING GIST (coordinates);
CREATE INDEX idx_cities_country ON cities(country);

-- POIs table (core data)
CREATE TABLE pois (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    city_id UUID REFERENCES cities(id),
    
    -- Identifiers
    name VARCHAR(500) NOT NULL,
    wikidata_id VARCHAR(20),
    google_place_id VARCHAR(255),
    wikipedia_url VARCHAR(500),
    
    -- Location
    coordinates GEOGRAPHY(POINT, 4326) NOT NULL,
    address TEXT,
    
    -- Historical/Cultural Data
    year_built INTEGER,
    year_built_circa BOOLEAN DEFAULT FALSE,  -- true if approximate
    architect VARCHAR(255),
    architectural_style VARCHAR(255),
    heritage_status VARCHAR(255),  -- e.g., "UNESCO World Heritage Site"
    
    -- Content
    summary TEXT,  -- LLM-generated 3-line summary
    wikipedia_extract TEXT,  -- Raw extract for regeneration
    
    -- Media
    image_url VARCHAR(500),
    image_attribution TEXT,
    
    -- Practical Info
    poi_type VARCHAR(50),  -- cathedral, museum, monument, etc.
    estimated_visit_duration INTEGER DEFAULT 60,  -- minutes
    
    -- Metadata
    data_quality_score DECIMAL(3,2),  -- 0.00 to 1.00
    data_source VARCHAR(50),  -- wikidata, google, manual
    last_verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_pois_city ON pois(city_id);
CREATE INDEX idx_pois_coordinates ON pois USING GIST (coordinates);
CREATE INDEX idx_pois_wikidata ON pois(wikidata_id);
CREATE INDEX idx_pois_type ON pois(poi_type);

-- Users table (Phase 2)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    display_name VARCHAR(100),
    auth_provider VARCHAR(50),  -- google, apple, email
    auth_provider_id VARCHAR(255),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trips table
CREATE TABLE trips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),  -- NULL for anonymous trips
    device_id VARCHAR(255),  -- For anonymous trip persistence
    
    name VARCHAR(255) NOT NULL,
    destination_city_id UUID REFERENCES cities(id),
    start_date DATE,
    end_date DATE,
    
    status VARCHAR(20) DEFAULT 'draft',  -- draft, planned, completed
    share_token VARCHAR(64) UNIQUE,  -- For sharing trips
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_trips_user ON trips(user_id);
CREATE INDEX idx_trips_device ON trips(device_id);
CREATE INDEX idx_trips_share ON trips(share_token);

-- Trip POIs (many-to-many with order)
CREATE TABLE trip_pois (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID REFERENCES trips(id) ON DELETE CASCADE,
    poi_id UUID REFERENCES pois(id),
    
    day_number INTEGER,  -- Which day of the trip (1, 2, 3...)
    order_in_day INTEGER,  -- Order within the day
    
    user_notes TEXT,
    is_must_see BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_trip_pois_trip ON trip_pois(trip_id);
CREATE UNIQUE INDEX idx_trip_pois_unique ON trip_pois(trip_id, poi_id);

-- Itineraries table (generated schedules)
CREATE TABLE itineraries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID REFERENCES trips(id) ON DELETE CASCADE,
    
    day_number INTEGER NOT NULL,
    date DATE,
    
    schedule JSONB NOT NULL,  -- Array of scheduled POIs with times
    total_duration_minutes INTEGER,
    total_travel_minutes INTEGER,
    
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(trip_id, day_number)
);

-- API cache table (for expensive external API calls)
CREATE TABLE api_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    response JSONB NOT NULL,
    source VARCHAR(50),  -- google_places, wikidata, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX idx_api_cache_expires ON api_cache(expires_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to all tables with updated_at
CREATE TRIGGER update_cities_updated_at BEFORE UPDATE ON cities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_pois_updated_at BEFORE UPDATE ON pois
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_trips_updated_at BEFORE UPDATE ON trips
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### 7.2 Redis Cache Structure

```
# POI data cache (30 day TTL)
poi:{poi_id} -> JSON string of full POI object
poi:wikidata:{wikidata_id} -> poi_id (lookup index)
poi:google:{google_place_id} -> poi_id (lookup index)

# City POI list cache (24 hour TTL)
city:{city_id}:pois -> JSON array of POI IDs

# API response cache (varies by endpoint)
api:google:place:{place_id} -> Google Places response
api:wikidata:{query_hash} -> Wikidata SPARQL response
api:wikipedia:{title} -> Wikipedia extract

# Rate limiting
ratelimit:{ip}:{endpoint} -> request count (1 minute window)
ratelimit:{device_id}:{endpoint} -> request count (daily window)

# Session data (for future auth)
session:{token} -> user_id and metadata
```

---

## 8. API Endpoints Design

### 8.1 REST API Specification

```yaml
openapi: 3.0.0
info:
  title: travelers.ai API
  version: 1.0.0
  description: AI-powered travel planning with cultural context

servers:
  - url: https://api.travelers.ai/v1

paths:
  # ============== CITIES ==============
  /cities/search:
    get:
      summary: Search for cities
      parameters:
        - name: q
          in: query
          required: true
          schema:
            type: string
          description: Search query (city name)
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
            maximum: 50
      responses:
        200:
          description: List of matching cities
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/City'

  /cities/{city_id}:
    get:
      summary: Get city details
      parameters:
        - name: city_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        200:
          description: City details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/City'

  # ============== POIs ==============
  /pois:
    get:
      summary: Get POIs for a city
      parameters:
        - name: city_id
          in: query
          required: true
          schema:
            type: string
            format: uuid
        - name: type
          in: query
          schema:
            type: string
            enum: [cathedral, museum, monument, palace, park, all]
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
        - name: offset
          in: query
          schema:
            type: integer
            default: 0
      responses:
        200:
          description: List of POIs
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items:
                      $ref: '#/components/schemas/POI'
                  total:
                    type: integer
                  has_more:
                    type: boolean

  /pois/{poi_id}:
    get:
      summary: Get POI details with info card
      parameters:
        - name: poi_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        200:
          description: POI details including summary
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/POIDetail'

  /pois/search:
    get:
      summary: Search for POIs by name
      parameters:
        - name: q
          in: query
          required: true
          schema:
            type: string
        - name: city_id
          in: query
          schema:
            type: string
            format: uuid
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
      responses:
        200:
          description: Matching POIs
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/POI'

  # ============== TRIPS ==============
  /trips:
    get:
      summary: Get user's trips
      parameters:
        - name: device_id
          in: header
          required: true
          schema:
            type: string
        - name: status
          in: query
          schema:
            type: string
            enum: [draft, planned, completed, all]
            default: all
      responses:
        200:
          description: List of trips
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Trip'
    
    post:
      summary: Create a new trip
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - name
                - destination_city_id
              properties:
                name:
                  type: string
                destination_city_id:
                  type: string
                  format: uuid
                start_date:
                  type: string
                  format: date
                end_date:
                  type: string
                  format: date
      responses:
        201:
          description: Trip created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Trip'

  /trips/{trip_id}:
    get:
      summary: Get trip details
      parameters:
        - name: trip_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        200:
          description: Trip details with POIs
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TripDetail'
    
    patch:
      summary: Update trip
      parameters:
        - name: trip_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                start_date:
                  type: string
                  format: date
                end_date:
                  type: string
                  format: date
                status:
                  type: string
                  enum: [draft, planned, completed]
      responses:
        200:
          description: Trip updated
    
    delete:
      summary: Delete trip
      parameters:
        - name: trip_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        204:
          description: Trip deleted

  /trips/{trip_id}/pois:
    post:
      summary: Add POI to trip
      parameters:
        - name: trip_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - poi_id
              properties:
                poi_id:
                  type: string
                  format: uuid
                day_number:
                  type: integer
                is_must_see:
                  type: boolean
                user_notes:
                  type: string
      responses:
        201:
          description: POI added to trip
    
    delete:
      summary: Remove POI from trip
      parameters:
        - name: trip_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
        - name: poi_id
          in: query
          required: true
          schema:
            type: string
            format: uuid
      responses:
        204:
          description: POI removed from trip

  # ============== ITINERARIES ==============
  /trips/{trip_id}/itinerary:
    post:
      summary: Generate itinerary for trip
      parameters:
        - name: trip_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                start_time:
                  type: string
                  default: "09:00"
                end_time:
                  type: string
                  default: "18:00"
                start_location:
                  type: object
                  properties:
                    lat:
                      type: number
                    lng:
                      type: number
      responses:
        200:
          description: Generated itinerary
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Itinerary'
    
    get:
      summary: Get existing itinerary
      parameters:
        - name: trip_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
        - name: day
          in: query
          schema:
            type: integer
      responses:
        200:
          description: Itinerary details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Itinerary'

  /trips/{trip_id}/share:
    post:
      summary: Generate share link for trip
      parameters:
        - name: trip_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        200:
          description: Share link generated
          content:
            application/json:
              schema:
                type: object
                properties:
                  share_url:
                    type: string
                  expires_at:
                    type: string
                    format: date-time

  /shared/{share_token}:
    get:
      summary: View shared trip (no auth required)
      parameters:
        - name: share_token
          in: path
          required: true
          schema:
            type: string
      responses:
        200:
          description: Shared trip details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TripDetail'

components:
  schemas:
    City:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        country:
          type: string
        country_code:
          type: string
        coordinates:
          $ref: '#/components/schemas/Coordinates'
        timezone:
          type: string

    Coordinates:
      type: object
      properties:
        lat:
          type: number
        lng:
          type: number

    POI:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        coordinates:
          $ref: '#/components/schemas/Coordinates'
        poi_type:
          type: string
        year_built:
          type: integer
        image_url:
          type: string
        data_quality_score:
          type: number

    POIDetail:
      allOf:
        - $ref: '#/components/schemas/POI'
        - type: object
          properties:
            architect:
              type: string
            architectural_style:
              type: string
            heritage_status:
              type: string
            summary:
              type: string
            wikipedia_url:
              type: string
            estimated_visit_duration:
              type: integer
            address:
              type: string

    Trip:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        destination_city:
          $ref: '#/components/schemas/City'
        start_date:
          type: string
          format: date
        end_date:
          type: string
          format: date
        status:
          type: string
        poi_count:
          type: integer
        created_at:
          type: string
          format: date-time

    TripDetail:
      allOf:
        - $ref: '#/components/schemas/Trip'
        - type: object
          properties:
            pois:
              type: array
              items:
                type: object
                properties:
                  poi:
                    $ref: '#/components/schemas/POIDetail'
                  day_number:
                    type: integer
                  order_in_day:
                    type: integer
                  is_must_see:
                    type: boolean
                  user_notes:
                    type: string

    Itinerary:
      type: object
      properties:
        trip_id:
          type: string
          format: uuid
        days:
          type: array
          items:
            type: object
            properties:
              day_number:
                type: integer
              date:
                type: string
                format: date
              total_duration_minutes:
                type: integer
              total_travel_minutes:
                type: integer
              schedule:
                type: array
                items:
                  type: object
                  properties:
                    poi:
                      $ref: '#/components/schemas/POIDetail'
                    arrival:
                      type: string
                    departure:
                      type: string
                    travel_from_previous_minutes:
                      type: integer
```

---

## 9. Cost Analysis

### 9.1 Per-Request Cost Breakdown

| Operation | API Used | Cost |
|-----------|----------|------|
| City search | Google Places Text Search | $0.032 |
| POI identification (new) | Google Places Text Search | $0.032 |
| POI identification (cached) | Local DB | $0.00 |
| Wikidata query | Wikidata SPARQL | $0.00 |
| Wikipedia extract | Wikipedia API | $0.00 |
| LLM summary generation | GPT-4o-mini (~500 tokens) | $0.0003 |
| Route calculation (8 POIs) | OpenRouteService | $0.00 |
| Route calculation (8 POIs) | Google Directions (alternative) | $0.005 |

### 9.2 Per-User Session Cost

**Example Session:** User searches 1 city, views 8 POIs, generates itinerary

| Scenario | Cost |
|----------|------|
| All POIs cached | ~$0.04 |
| 2 new POIs need processing | ~$0.10 |
| All 8 POIs are new | ~$0.30 |

### 9.3 Infrastructure Costs

| Component | Service | Monthly Cost |
|-----------|---------|--------------|
| Backend hosting | Railway / Render | $20-50 |
| PostgreSQL | Railway / Supabase | $25-50 |
| Redis | Upstash / Railway | $10-20 |
| Object storage | Cloudflare R2 | $5-15 |
| Domain + SSL | Cloudflare | $15/year |
| **Total infrastructure** | | **$60-135/month** |

### 9.4 Cost Optimization Strategies

1. **Aggressive caching:** 30-day TTL for POI data (historical facts don't change)
2. **Pre-populate popular cities:** Generate POI data for top 100 tourist cities upfront
3. **Use free APIs first:** Wikidata + Wikipedia before Google Places
4. **Batch LLM calls:** Generate summaries in batches during off-peak hours
5. **CDN for images:** Cache Wikimedia Commons images via Cloudflare

---

## 10. Implementation Roadmap

### 10.1 Phase 1: MVP

#### Backend Foundation
- [ ] Set up FastAPI project structure
- [ ] Configure PostgreSQL with schema
- [ ] Implement Wikidata SPARQL client
- [ ] Implement Wikipedia API client
- [ ] Implement basic POI data pipeline
- [ ] Set up Redis caching

#### Core API & LLM Integration
- [ ] Implement city search endpoint
- [ ] Implement POI listing endpoint
- [ ] Implement POI detail endpoint with LLM summaries
- [ ] Implement trip CRUD endpoints
- [ ] Implement itinerary generation
- [ ] Add Google Places API integration (fallback)

#### Mobile App MVP
- [ ] Set up React Native (Expo) project
- [ ] Implement city search screen
- [ ] Implement map view with POI markers
- [ ] Implement POI info card component
- [ ] Implement trip builder screen
- [ ] Implement itinerary view screen
- [ ] Local storage for trips (AsyncStorage)

### 10.2 Phase 2: Polish & Launch Prep

#### UX Polish
- [ ] Refine info card design
- [ ] Add loading states and error handling
- [ ] Implement share functionality
- [ ] Add PDF export for itineraries
- [ ] Offline data caching for active trip

#### Launch Preparation
- [ ] Pre-populate data for 20 major tourist cities
- [ ] Set up monitoring (Sentry, analytics)
- [ ] App Store / Play Store submission
- [ ] Beta testing
- [ ] Performance optimization

### 10.3 Phase 3: Growth Features

- [ ] User accounts (Firebase Auth or similar)
- [ ] Affiliate link integration (Viator, GetYourGuide)
- [ ] Multiple trips per user
- [ ] Collaborative trip editing
- [ ] Push notifications for trip reminders
- [ ] Web version (Next.js)

---

## 11. Risk Assessment

### 11.1 Technical Risks

| Risk | Mitigation |
|------|------------|
| Wikidata gaps for obscure POIs | Graceful fallback UI, show "basic info only" |
| LLM hallucinations in summaries | Always show structured data separately, cite sources |
| Google API costs spike | Aggressive caching, usage alerts, budget caps |
| Wikipedia API rate limits | Request caching, respect rate limits |
| Mobile app performance issues | Lazy loading, pagination, image optimization |

### 11.2 Business Risks

| Risk | Mitigation |
|------|------------|
| Low user adoption | Focus on specific niche (cultural travelers), strong SEO |
| Competitors copy feature | Build data quality moat, community features |
| User expects booking features | Clear positioning, link out to booking sites |
| Negative reviews for data gaps | Transparent quality scores, user feedback loop |

### 11.3 Data Quality Risks

| Risk | Mitigation |
|------|------------|
| Incorrect historical dates | Cross-reference multiple sources, user reports |
| Outdated opening hours | Don't show hours, link to official sites |
| Missing POIs for small cities | Allow user submissions, prioritize coverage |
| LLM-generated factual errors | Human review for popular POIs, feedback system |

---

## Appendix: Code Examples

### A.1 Wikidata Client (Python)

```python
# wikidata_client.py

import httpx
from typing import Optional, Dict, Any
from pydantic import BaseModel

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

class WikidataPOIData(BaseModel):
    wikidata_id: str
    name: str
    inception: Optional[int] = None
    inception_circa: bool = False
    architect: Optional[str] = None
    architectural_style: Optional[str] = None
    heritage_status: Optional[str] = None
    image_url: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None


async def get_poi_by_name(poi_name: str, city_name: str) -> Optional[WikidataPOIData]:
    """
    Query Wikidata for POI information by name and city.
    """
    query = f"""
    SELECT ?item ?itemLabel ?inception ?architectLabel ?styleLabel 
           ?heritageLabel ?image ?coords
    WHERE {{
      ?item rdfs:label "{poi_name}"@en .
      ?item wdt:P131* ?city .
      ?city rdfs:label "{city_name}"@en .
      
      OPTIONAL {{ ?item wdt:P571 ?inception }}
      OPTIONAL {{ ?item wdt:P84 ?architect }}
      OPTIONAL {{ ?item wdt:P149 ?style }}
      OPTIONAL {{ ?item wdt:P1435 ?heritage }}
      OPTIONAL {{ ?item wdt:P18 ?image }}
      OPTIONAL {{ ?item wdt:P625 ?coords }}
      
      SERVICE wikibase:label {{ 
        bd:serviceParam wikibase:language "en". 
      }}
    }}
    LIMIT 1
    """
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            WIKIDATA_ENDPOINT,
            params={"query": query, "format": "json"},
            headers={"Accept": "application/sparql-results+json"},
            timeout=30.0
        )
        response.raise_for_status()
        
    data = response.json()
    results = data.get("results", {}).get("bindings", [])
    
    if not results:
        return None
    
    result = results[0]
    
    # Parse coordinates from Point format
    coords = None
    if "coords" in result:
        coord_str = result["coords"]["value"]
        # Format: "Point(-3.5986 37.1761)"
        if coord_str.startswith("Point("):
            parts = coord_str[6:-1].split()
            coords = {"lng": float(parts[0]), "lat": float(parts[1])}
    
    # Parse inception year
    inception = None
    inception_circa = False
    if "inception" in result:
        inception_str = result["inception"]["value"]
        # Handle full datetime format
        if "T" in inception_str:
            inception = int(inception_str.split("-")[0])
        else:
            inception = int(inception_str)
    
    return WikidataPOIData(
        wikidata_id=result["item"]["value"].split("/")[-1],
        name=result.get("itemLabel", {}).get("value", poi_name),
        inception=inception,
        inception_circa=inception_circa,
        architect=result.get("architectLabel", {}).get("value"),
        architectural_style=result.get("styleLabel", {}).get("value"),
        heritage_status=result.get("heritageLabel", {}).get("value"),
        image_url=result.get("image", {}).get("value"),
        coordinates=coords
    )


async def get_tourist_attractions_in_city(
    city_wikidata_id: str, 
    limit: int = 50
) -> list[Dict[str, Any]]:
    """
    Get list of tourist attractions in a city by Wikidata ID.
    """
    query = f"""
    SELECT DISTINCT ?attraction ?attractionLabel ?coords ?inception 
                    ?architectLabel ?styleLabel ?image
    WHERE {{
      ?attraction (wdt:P31/wdt:P279*) wd:Q570116 .
      ?attraction wdt:P131* wd:{city_wikidata_id} .
      
      OPTIONAL {{ ?attraction wdt:P625 ?coords }}
      OPTIONAL {{ ?attraction wdt:P571 ?inception }}
      OPTIONAL {{ ?attraction wdt:P84 ?architect }}
      OPTIONAL {{ ?attraction wdt:P149 ?style }}
      OPTIONAL {{ ?attraction wdt:P18 ?image }}
      
      SERVICE wikibase:label {{ 
        bd:serviceParam wikibase:language "en". 
      }}
    }}
    LIMIT {limit}
    """
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            WIKIDATA_ENDPOINT,
            params={"query": query, "format": "json"},
            headers={"Accept": "application/sparql-results+json"},
            timeout=30.0
        )
        response.raise_for_status()
    
    data = response.json()
    results = data.get("results", {}).get("bindings", [])
    
    attractions = []
    for result in results:
        # Parse coordinates
        coords = None
        if "coords" in result:
            coord_str = result["coords"]["value"]
            if coord_str.startswith("Point("):
                parts = coord_str[6:-1].split()
                coords = {"lng": float(parts[0]), "lat": float(parts[1])}
        
        attractions.append({
            "wikidata_id": result["attraction"]["value"].split("/")[-1],
            "name": result.get("attractionLabel", {}).get("value"),
            "coordinates": coords,
            "inception": result.get("inception", {}).get("value"),
            "architect": result.get("architectLabel", {}).get("value"),
            "style": result.get("styleLabel", {}).get("value"),
            "image_url": result.get("image", {}).get("value"),
        })
    
    return attractions
```

### A.2 Wikipedia Client (Python)

```python
# wikipedia_client.py

import httpx
from typing import Optional

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"


async def get_article_extract(title: str, sentences: int = 5) -> Optional[str]:
    """
    Get the introductory extract from a Wikipedia article.
    """
    params = {
        "action": "query",
        "titles": title,
        "prop": "extracts",
        "exintro": "true",
        "explaintext": "true",
        "exsentences": sentences,
        "format": "json",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            WIKIPEDIA_API, 
            params=params, 
            timeout=15.0
        )
        response.raise_for_status()
    
    data = response.json()
    pages = data.get("query", {}).get("pages", {})
    
    for page_id, page_data in pages.items():
        if page_id != "-1":  # -1 means page not found
            return page_data.get("extract")
    
    return None


async def search_nearby_landmarks(
    lat: float, 
    lng: float, 
    radius: int = 10000,
    limit: int = 50
) -> list[dict]:
    """
    Search for Wikipedia articles about landmarks near coordinates.
    """
    params = {
        "action": "query",
        "list": "geosearch",
        "gscoord": f"{lat}|{lng}",
        "gsradius": radius,
        "gslimit": limit,
        "gsprop": "type|name|dim|country|region",
        "format": "json",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            WIKIPEDIA_API, 
            params=params, 
            timeout=15.0
        )
        response.raise_for_status()
    
    data = response.json()
    results = data.get("query", {}).get("geosearch", [])
    
    landmarks = []
    for result in results:
        # Filter for landmark types
        poi_type = result.get("type", "")
        if poi_type in ["landmark", "monument", "building", "church", "castle"]:
            landmarks.append({
                "title": result.get("title"),
                "wikipedia_page_id": result.get("pageid"),
                "coordinates": {
                    "lat": result.get("lat"),
                    "lng": result.get("lon")
                },
                "type": poi_type,
                "distance_meters": result.get("dist"),
            })
    
    return landmarks
```

### A.3 LLM Summary Generator (Python)

```python
# summary_generator.py

from openai import AsyncOpenAI
from typing import Optional
from pydantic import BaseModel

client = AsyncOpenAI()

class POISummaryInput(BaseModel):
    name: str
    year_built: Optional[int] = None
    architect: Optional[str] = None
    architectural_style: Optional[str] = None
    heritage_status: Optional[str] = None
    wikipedia_extract: Optional[str] = None


async def generate_poi_summary(poi: POISummaryInput) -> str:
    """
    Generate a concise 3-sentence summary for a POI using GPT-4o-mini.
    """
    # Build context from available data
    context_parts = []
    if poi.year_built:
        context_parts.append(f"Built: {poi.year_built}")
    if poi.architect:
        context_parts.append(f"Architect: {poi.architect}")
    if poi.architectural_style:
        context_parts.append(f"Style: {poi.architectural_style}")
    if poi.heritage_status:
        context_parts.append(f"Status: {poi.heritage_status}")
    
    context = "\n".join(context_parts) if context_parts else "Limited data available"
    
    extract = poi.wikipedia_extract or "No Wikipedia description available."
    
    prompt = f"""You are a travel guide writer creating concise, memorable descriptions for tourists.

Given this information about "{poi.name}":

STRUCTURED DATA:
{context}

WIKIPEDIA EXTRACT:
{extract}

Write a 3-sentence summary (maximum 60 words total) that a tourist would find useful and memorable.

Requirements:
1. First sentence: Historical context or origin story
2. Second sentence: One visual/architectural highlight to look for when visiting
3. Third sentence: A practical tip, lesser-known fact, or what makes it special

Style guidelines:
- Engaging and conversational tone
- Avoid generic phrases like "must-see", "don't miss", "iconic"
- Include specific details that make the place unique
- If data is limited, focus on what IS known without apologizing for gaps

Respond with ONLY the 3-sentence summary, no additional text."""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.7,
    )
    
    return response.choices[0].message.content.strip()


async def generate_fallback_summary(poi_name: str, poi_type: str) -> str:
    """
    Generate a minimal fallback when structured data is unavailable.
    """
    type_descriptions = {
        "cathedral": "a historic cathedral worth exploring",
        "church": "a historic church with architectural significance",
        "museum": "a museum housing notable collections",
        "palace": "a historic palace with rich heritage",
        "castle": "a castle with centuries of history",
        "monument": "a notable monument marking significant history",
        "park": "a scenic park offering natural beauty",
        "default": "a notable point of interest",
    }
    
    desc = type_descriptions.get(poi_type, type_descriptions["default"])
    
    return (
        f"{poi_name} is {desc}. "
        f"Check local visitor information for current opening hours and guided tour options. "
        f"Consider combining your visit with nearby attractions for a richer experience."
    )
```

### A.4 POI Service (Python)

```python
# poi_service.py

from typing import Optional
from uuid import UUID, uuid4
import json

from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import POI, City
from .wikidata_client import get_poi_by_name, WikidataPOIData
from .wikipedia_client import get_article_extract
from .summary_generator import generate_poi_summary, POISummaryInput

CACHE_TTL = 60 * 60 * 24 * 30  # 30 days


class POIService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.db = db
        self.redis = redis
    
    async def get_poi_detail(self, poi_id: UUID) -> Optional[dict]:
        """
        Get full POI details including summary.
        Returns cached data if available, otherwise fetches and generates.
        """
        # Check cache first
        cache_key = f"poi:{poi_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Fetch from database
        result = await self.db.execute(
            select(POI).where(POI.id == poi_id)
        )
        poi = result.scalar_one_or_none()
        
        if not poi:
            return None
        
        # If summary exists and is fresh, return
        if poi.summary and poi.last_verified_at:
            poi_dict = self._poi_to_dict(poi)
            await self.redis.setex(cache_key, CACHE_TTL, json.dumps(poi_dict))
            return poi_dict
        
        # Otherwise, enrich with external data
        enriched = await self._enrich_poi(poi)
        
        # Update database
        for key, value in enriched.items():
            if hasattr(poi, key):
                setattr(poi, key, value)
        await self.db.commit()
        
        # Cache and return
        poi_dict = self._poi_to_dict(poi)
        await self.redis.setex(cache_key, CACHE_TTL, json.dumps(poi_dict))
        return poi_dict
    
    async def _enrich_poi(self, poi: POI) -> dict:
        """
        Fetch additional data from Wikidata/Wikipedia and generate summary.
        """
        enrichments = {}
        
        # Try Wikidata if we have the ID or can find it
        wikidata_data = None
        if poi.wikidata_id:
            # Fetch fresh data
            pass  # TODO: implement refresh
        else:
            # Try to find by name
            city_result = await self.db.execute(
                select(City).where(City.id == poi.city_id)
            )
            city = city_result.scalar_one_or_none()
            if city:
                wikidata_data = await get_poi_by_name(poi.name, city.name)
        
        if wikidata_data:
            enrichments.update({
                "wikidata_id": wikidata_data.wikidata_id,
                "year_built": wikidata_data.inception,
                "architect": wikidata_data.architect,
                "architectural_style": wikidata_data.architectural_style,
                "heritage_status": wikidata_data.heritage_status,
                "image_url": wikidata_data.image_url,
            })
        
        # Fetch Wikipedia extract
        wiki_title = poi.name.replace(" ", "_")
        extract = await get_article_extract(wiki_title)
        if extract:
            enrichments["wikipedia_extract"] = extract
            enrichments["wikipedia_url"] = f"https://en.wikipedia.org/wiki/{wiki_title}"
        
        # Generate summary
        summary_input = POISummaryInput(
            name=poi.name,
            year_built=enrichments.get("year_built") or poi.year_built,
            architect=enrichments.get("architect") or poi.architect,
            architectural_style=enrichments.get("architectural_style") or poi.architectural_style,
            heritage_status=enrichments.get("heritage_status") or poi.heritage_status,
            wikipedia_extract=enrichments.get("wikipedia_extract") or poi.wikipedia_extract,
        )
        
        summary = await generate_poi_summary(summary_input)
        enrichments["summary"] = summary
        
        # Calculate quality score
        enrichments["data_quality_score"] = self._calculate_quality_score(
            {**self._poi_to_dict(poi), **enrichments}
        )
        
        return enrichments
    
    def _calculate_quality_score(self, poi_data: dict) -> float:
        """Calculate data completeness score (0.0 to 1.0)."""
        weights = {
            "name": 0.15,
            "coordinates": 0.20,
            "year_built": 0.15,
            "architect": 0.10,
            "architectural_style": 0.10,
            "summary": 0.15,
            "image_url": 0.10,
            "wikipedia_url": 0.05,
        }
        
        score = 0.0
        for field, weight in weights.items():
            if poi_data.get(field):
                score += weight
        
        return round(score, 2)
    
    def _poi_to_dict(self, poi: POI) -> dict:
        """Convert POI model to dictionary."""
        return {
            "id": str(poi.id),
            "name": poi.name,
            "coordinates": {
                "lat": poi.coordinates.y if poi.coordinates else None,
                "lng": poi.coordinates.x if poi.coordinates else None,
            },
            "year_built": poi.year_built,
            "architect": poi.architect,
            "architectural_style": poi.architectural_style,
            "heritage_status": poi.heritage_status,
            "summary": poi.summary,
            "image_url": poi.image_url,
            "wikipedia_url": poi.wikipedia_url,
            "poi_type": poi.poi_type,
            "estimated_visit_duration": poi.estimated_visit_duration,
            "data_quality_score": poi.data_quality_score,
        }
```

### A.5 Itinerary Generator (Python)

```python
# itinerary_generator.py

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import httpx

OPENROUTE_API = "https://api.openrouteservice.org/v2/matrix/foot-walking"


class ItineraryGenerator:
    def __init__(self, openroute_api_key: Optional[str] = None):
        self.openroute_api_key = openroute_api_key
    
    async def generate_itinerary(
        self,
        pois: List[dict],
        date: str,
        start_time: str = "09:00",
        end_time: str = "18:00",
        start_location: Optional[dict] = None,
    ) -> dict:
        """
        Generate an optimized daily itinerary for given POIs.
        """
        if not pois:
            return {"error": "No POIs provided"}
        
        # Use first POI as start if no start location
        if not start_location and pois:
            start_location = pois[0]["coordinates"]
        
        # Get travel time matrix
        all_locations = [start_location] + [p["coordinates"] for p in pois]
        travel_matrix = await self._get_travel_matrix(all_locations)
        
        # Optimize route order (simple nearest neighbor)
        optimized_order = self._optimize_route(pois, travel_matrix)
        
        # Build schedule
        schedule = self._build_schedule(
            pois=[pois[i] for i in optimized_order],
            travel_matrix=travel_matrix,
            optimized_order=optimized_order,
            start_time=start_time,
        )
        
        # Calculate totals
        total_travel = sum(item["travel_from_previous_minutes"] for item in schedule)
        total_duration = sum(
            item["poi"]["estimated_visit_duration"] 
            for item in schedule
        ) + total_travel
        
        return {
            "date": date,
            "start_time": start_time,
            "total_duration_minutes": total_duration,
            "total_travel_minutes": total_travel,
            "schedule": schedule,
        }
    
    async def _get_travel_matrix(
        self, 
        locations: List[dict]
    ) -> List[List[int]]:
        """
        Get walking time matrix between all locations.
        Returns matrix of travel times in minutes.
        """
        if not self.openroute_api_key:
            # Return estimated walking times (rough estimate)
            return self._estimate_walking_matrix(locations)
        
        # Format coordinates for OpenRouteService: [lng, lat]
        coords = [[loc["lng"], loc["lat"]] for loc in locations]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENROUTE_API,
                json={"locations": coords, "metrics": ["duration"]},
                headers={
                    "Authorization": self.openroute_api_key,
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
            response.raise_for_status()
        
        data = response.json()
        durations = data.get("durations", [])
        
        # Convert seconds to minutes
        return [
            [int(d / 60) if d else 0 for d in row]
            for row in durations
        ]
    
    def _estimate_walking_matrix(
        self, 
        locations: List[dict]
    ) -> List[List[int]]:
        """
        Estimate walking times based on straight-line distance.
        Assumes 5 km/h walking speed with 1.3x factor for non-straight routes.
        """
        import math
        
        def haversine_km(loc1: dict, loc2: dict) -> float:
            R = 6371  # Earth radius in km
            lat1, lat2 = math.radians(loc1["lat"]), math.radians(loc2["lat"])
            dlat = lat2 - lat1
            dlng = math.radians(loc2["lng"] - loc1["lng"])
            
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
            c = 2 * math.asin(math.sqrt(a))
            return R * c
        
        n = len(locations)
        matrix = []
        
        for i in range(n):
            row = []
            for j in range(n):
                if i == j:
                    row.append(0)
                else:
                    dist_km = haversine_km(locations[i], locations[j])
                    # Walking time: distance * 1.3 (route factor) / 5 km/h * 60 min
                    walk_minutes = int(dist_km * 1.3 / 5 * 60)
                    row.append(max(walk_minutes, 1))  # Minimum 1 minute
            matrix.append(row)
        
        return matrix
    
    def _optimize_route(
        self, 
        pois: List[dict], 
        travel_matrix: List[List[int]]
    ) -> List[int]:
        """
        Optimize POI visit order using nearest neighbor algorithm.
        Returns list of indices in optimized order.
        """
        n = len(pois)
        if n <= 1:
            return list(range(n))
        
        visited = [False] * n
        order = []
        current = 0  # Start from first location (start_location in matrix)
        
        for _ in range(n):
            # Find nearest unvisited POI
            best_idx = -1
            best_time = float('inf')
            
            for i in range(n):
                if not visited[i]:
                    # +1 because matrix[0] is start_location
                    travel_time = travel_matrix[current][i + 1]
                    if travel_time < best_time:
                        best_time = travel_time
                        best_idx = i
            
            if best_idx >= 0:
                visited[best_idx] = True
                order.append(best_idx)
                current = best_idx + 1  # Update current position in matrix
        
        return order
    
    def _build_schedule(
        self,
        pois: List[dict],
        travel_matrix: List[List[int]],
        optimized_order: List[int],
        start_time: str,
    ) -> List[dict]:
        """
        Build detailed schedule with arrival/departure times.
        """
        schedule = []
        current_time = datetime.strptime(start_time, "%H:%M")
        
        # Matrix index: 0 is start location, 1+ are POIs in original order
        prev_matrix_idx = 0  # Start from start_location
        
        for i, poi_idx in enumerate(optimized_order):
            poi = pois[poi_idx]
            
            # Get travel time from previous location
            curr_matrix_idx = poi_idx + 1  # +1 because matrix[0] is start
            travel_minutes = travel_matrix[prev_matrix_idx][curr_matrix_idx]
            
            # Calculate times
            arrival = current_time + timedelta(minutes=travel_minutes)
            visit_duration = poi.get("estimated_visit_duration", 60)
            departure = arrival + timedelta(minutes=visit_duration)
            
            schedule.append({
                "order": i + 1,
                "poi": poi,
                "arrival": arrival.strftime("%H:%M"),
                "departure": departure.strftime("%H:%M"),
                "travel_from_previous_minutes": travel_minutes,
            })
            
            current_time = departure
            prev_matrix_idx = curr_matrix_idx
        
        return schedule
```

---

## Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/travelers
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=sk-...
GOOGLE_PLACES_API_KEY=AIza...  # Optional, for fallback
OPENROUTE_API_KEY=...  # Optional, for accurate walking times
```
