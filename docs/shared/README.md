# Shared Package Documentation

The `@travelers/shared` package contains TypeScript types, translations, and utility functions shared between packages.

## Directory Structure

```
packages/shared/
├── src/
│   ├── index.ts           # Main exports
│   ├── types/
│   │   └── index.ts       # Type definitions
│   ├── i18n/
│   │   ├── index.ts       # Translation function
│   │   ├── en.ts          # English translations
│   │   └── es.ts          # Spanish translations
│   └── utils/
│       └── index.ts       # Utility functions
├── tsup.config.ts         # Build configuration
└── package.json
```

## Installation

This package is installed automatically via pnpm workspaces:

```json
{
  "dependencies": {
    "@travelers/shared": "workspace:*"
  }
}
```

## Types

Types match the API response format (snake_case) for direct compatibility.

### Core Types

```typescript
interface Coordinates {
  lat: number;
  lng: number;
}

interface City {
  id: string;
  name: string;
  country: string;
  country_code: string | null;
  coordinates: Coordinates | null;
  timezone: string | null;
  wikidata_id: string | null;
  google_place_id: string | null;
}

interface POI {
  id: string;
  name: string;
  coordinates: Coordinates | null;
  poi_type: string | null;
  year_built: number | null;
  image_url: string | null;
  estimated_visit_duration: number;
}

interface POIDetail extends POI {
  city_id: string;
  wikidata_id: string | null;
  wikipedia_url: string | null;
  address: string | null;
  year_built_circa: boolean;
  architect: string | null;
  architectural_style: string | null;
  heritage_status: string | null;
  summary: string | null;
  wikipedia_extract: string | null;
  image_attribution: string | null;
  data_quality_score: number | null;
  last_verified_at: string | null;
}
```

### Response Types

```typescript
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  has_more: boolean;
}

interface SearchResponse<T> {
  items: T[];
  total: number;
}
```

### POI Types

```typescript
type POIType =
  | 'cathedral'
  | 'church'
  | 'museum'
  | 'palace'
  | 'castle'
  | 'monument'
  | 'park'
  | 'plaza'
  | 'bridge'
  | 'tower'
  | 'theater'
  | 'library'
  | 'university'
  | 'building'
  | 'government'
  | 'landmark'
  | 'other';
```

## Internationalization

### Translation Function

```typescript
import { t, type TranslationKey, type Language } from '@travelers/shared';

// Basic usage
t('app.tagline', 'en');  // "Discover the stories behind every place"
t('app.tagline', 'es');  // "Descubre las historias detrás de cada lugar"

// With parameters (for future use)
t('poi.placesFound', 'en', { count: 5 });
```

### Translation Keys

Keys are organized by section:

| Prefix | Description |
|--------|-------------|
| `app.*` | App-level strings |
| `common.*` | Common UI strings |
| `auth.*` | Authentication |
| `nav.*` | Navigation |
| `home.*` | Home screen |
| `city.*` | City-related |
| `poi.*` | POI-related |
| `poiType.*` | POI type names |
| `trip.*` | Trip management |
| `itinerary.*` | Itinerary |
| `export.*` | Export options |
| `settings.*` | Settings |
| `error.*` | Error messages |
| `sync.*` | Sync status |

### Adding Translations

1. Add key to `en.ts`:
```typescript
export const en = {
  // ...
  'mySection.myKey': 'English text',
} as const;
```

2. Add same key to `es.ts`:
```typescript
export const es = {
  // ...
  'mySection.myKey': 'Texto en español',
} as const;
```

## Utilities

### Distance Calculations

```typescript
import { haversineDistance, estimateWalkingMinutes } from '@travelers/shared';

// Calculate distance between two points
const km = haversineDistance(
  { lat: 41.3851, lng: 2.1734 },
  { lat: 41.4036, lng: 2.1744 }
);

// Estimate walking time (accounts for non-straight routes)
const minutes = estimateWalkingMinutes(km);
```

### Formatting

```typescript
import { formatDuration, formatDistance, formatDate, formatTime } from '@travelers/shared';

formatDuration(90, 'en');           // "1h 30min"
formatDuration(90, 'es');           // "1 h 30 min"

formatDistance(0.5);                // "500 m"
formatDistance(2.5);                // "2.5 km"

formatDate('2024-01-15', 'en');     // "Jan 15, 2024"
formatDate('2024-01-15', 'es');     // "15 ene 2024"

formatTime('14:30', 'en');          // "2:30 PM"
formatTime('14:30', 'es');          // "14:30"
```

### Token Generation

```typescript
import { generateShareToken } from '@travelers/shared';

const token = generateShareToken();  // "xK9mN2pL..."
```

## Building

```bash
cd packages/shared
pnpm build
```

Output:
- `dist/` - Compiled JavaScript (CJS + ESM)
- `dist/*.d.ts` - TypeScript declarations
