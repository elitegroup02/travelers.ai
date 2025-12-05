/**
 * Core entity types for travelers.ai
 *
 * These types match the API response format (snake_case) for direct compatibility.
 */

export interface Coordinates {
  lat: number;
  lng: number;
}

export interface City {
  id: string;
  name: string;
  country: string;
  country_code: string | null;
  coordinates: Coordinates | null;
  timezone: string | null;
  wikidata_id: string | null;
  google_place_id: string | null;
}

export interface POI {
  id: string;
  name: string;
  coordinates: Coordinates | null;
  poi_type: string | null;
  year_built: number | null;
  image_url: string | null;
  estimated_visit_duration: number;
}

export interface POIDetail extends POI {
  city_id: string;
  wikidata_id: string | null;
  google_place_id: string | null;
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

export type POIType =
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

export interface User {
  id: string;
  email: string;
  display_name: string | null;
  preferred_language: Language;
  created_at: string;
  updated_at: string;
}

export type Language = 'en' | 'es';

export interface Trip {
  id: string;
  user_id: string;
  name: string;
  destination_city_id: string;
  destination_city?: City;
  start_date: string | null;
  end_date: string | null;
  status: TripStatus;
  share_token: string | null;
  created_at: string;
  updated_at: string;
}

export type TripStatus = 'draft' | 'planned' | 'completed';

export interface TripPOI {
  id: string;
  trip_id: string;
  poi_id: string;
  poi?: POIDetail;
  day_number: number | null;
  order_in_day: number | null;
  user_notes: string | null;
  is_must_see: boolean;
  created_at: string;
}

export interface TripDetail extends Trip {
  pois: TripPOI[];
}

export interface Itinerary {
  trip_id: string;
  days: ItineraryDay[];
}

export interface ItineraryDay {
  day_number: number;
  date: string | null;
  total_duration_minutes: number;
  total_travel_minutes: number;
  schedule: ScheduleItem[];
}

export interface ScheduleItem {
  order: number;
  poi: POIDetail;
  arrival: string;
  departure: string;
  travel_from_previous_minutes: number;
  walking_route?: WalkingRoute;
}

export interface WalkingRoute {
  distance_meters: number;
  duration_minutes: number;
  polyline?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  has_more: boolean;
}

export interface SearchResponse<T> {
  items: T[];
  total: number;
}

export interface ApiError {
  detail: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  display_name?: string;
  preferred_language?: Language;
}
