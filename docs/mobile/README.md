# Mobile App Documentation

The travelers.ai mobile app is built with React Native and Expo, using TypeScript for type safety.

## Directory Structure

```
packages/mobile/
├── App.tsx                 # Root component
├── src/
│   ├── api/
│   │   └── client.ts      # Axios API client
│   ├── components/
│   │   ├── index.ts       # Component exports
│   │   └── POICard.tsx    # POI list item card
│   ├── hooks/
│   │   ├── index.ts       # Hook exports
│   │   └── useI18n.ts     # Internationalization hook
│   ├── navigation/
│   │   ├── index.ts       # Navigation exports
│   │   ├── RootNavigator.tsx  # Stack navigator
│   │   └── types.ts       # Navigation types
│   ├── screens/
│   │   ├── index.ts       # Screen exports
│   │   ├── HomeScreen.tsx
│   │   ├── CitySearchScreen.tsx
│   │   ├── POIListScreen.tsx
│   │   └── POIDetailScreen.tsx
│   └── stores/
│       ├── index.ts       # Store exports
│       ├── settings.ts    # App settings store
│       ├── cities.ts      # City search store
│       └── pois.ts        # POI data store
└── app.json               # Expo configuration
```

## State Management

The app uses Zustand for state management with three main stores:

### useSettingsStore

Persisted settings using AsyncStorage.

```typescript
interface SettingsState {
  language: 'en' | 'es' | null;
  setLanguage: (lang: Language) => void;
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}
```

### useCitiesStore

City search and selection state.

```typescript
interface CitiesState {
  searchResults: City[];
  searchQuery: string;
  isSearching: boolean;
  selectedCity: City | null;
  recentCities: City[];

  search: (query: string) => Promise<void>;
  selectCity: (cityId: string) => Promise<void>;
  clearSearch: () => void;
}
```

### usePOIsStore

POI list and detail state.

```typescript
interface POIsState {
  pois: POI[];
  selectedPOI: POIDetail | null;
  isLoading: boolean;
  hasMore: boolean;
  total: number;

  loadPOIsForCity: (cityId: string, options?) => Promise<void>;
  loadMorePOIs: (cityId: string, poiType?) => Promise<void>;
  selectPOI: (poiId: string, language: 'en' | 'es') => Promise<void>;
  searchPOIs: (query: string, cityId?) => Promise<void>;
  clearSelection: () => void;
}
```

## Navigation

Stack-based navigation with React Navigation.

```typescript
type RootStackParamList = {
  Home: undefined;
  CitySearch: undefined;
  POIList: { cityId: string; cityName: string };
  POIDetail: { poiId: string; poiName: string };
};
```

## Screens

### HomeScreen

Landing screen with:
- App tagline
- City search button
- Recent cities list (horizontal scroll)

### CitySearchScreen

City search with:
- Search input with auto-focus
- Live search results
- Loading indicator
- Empty state message

### POIListScreen

POI list for selected city:
- Total count header
- POI cards with image, name, type
- Infinite scroll pagination
- Loading indicator

### POIDetailScreen

POI detail with AI info card:
- Hero image
- POI name
- AI-generated summary (highlighted)
- Metadata grid (year, architect, style, heritage)
- Wikipedia extract
- Coordinates

## Components

### POICard

Card component for POI list items.

**Props:**
- `poi: POI` - POI data
- `onPress: () => void` - Tap handler

**Features:**
- Image with placeholder fallback
- Name (2-line truncation)
- Year and type badges
- Visit duration

## Hooks

### useI18n

Internationalization hook.

**Returns:**
- `language: 'en' | 'es'` - Current language
- `setLanguage: (lang) => void` - Change language
- `t: (key, params?) => string` - Translation function
- `translations` - All translations for current language

**Behavior:**
- Auto-detects device language
- Persists user preference
- Falls back to English for missing keys

## API Client

Axios-based client with typed functions.

```typescript
// Cities
searchCities(query, limit?): Promise<SearchResponse<City>>
getCity(cityId): Promise<City>
getNearbyCities(lat, lng, radiusKm?, limit?): Promise<...>

// POIs
getPOIsForCity(cityId, options?): Promise<PaginatedResponse<POI>>
getPOI(poiId, lang?): Promise<POIDetail>
searchPOIs(query, cityId?, limit?): Promise<SearchResponse<POI>>
getNearbyPOIs(lat, lng, radius?, limit?): Promise<...>
```

## Styling

The app uses a dark theme with StyleSheet:

```typescript
const colors = {
  background: '#0f0f23',
  cardBackground: '#1a1a2e',
  accent: '#4a90d9',
  textPrimary: '#fff',
  textSecondary: '#888',
  textMuted: '#666',
};
```

## Configuration

Environment variables via Expo:

```bash
EXPO_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Running the App

```bash
# Install dependencies
pnpm install

# Start Expo dev server
pnpm start

# Run on iOS simulator
pnpm ios

# Run on Android emulator
pnpm android
```
