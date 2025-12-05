import axios from 'axios';
import type { City, POI, POIDetail, PaginatedResponse, SearchResponse } from '@travelers/shared';

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function searchCities(query: string, limit = 10): Promise<SearchResponse<City>> {
  const response = await api.get('/cities/search', { params: { q: query, limit } });
  return response.data;
}

export async function getCity(cityId: string): Promise<City> {
  const response = await api.get(`/cities/${cityId}`);
  return response.data;
}

export async function getNearbyCities(
  lat: number,
  lng: number,
  radiusKm = 100,
  limit = 10
): Promise<SearchResponse<City & { distance_km: number }>> {
  const response = await api.get('/cities/nearby', {
    params: { lat, lng, radius_km: radiusKm, limit },
  });
  return response.data;
}

export async function getPOIsForCity(
  cityId: string,
  options?: { poiType?: string; limit?: number; offset?: number }
): Promise<PaginatedResponse<POI>> {
  const response = await api.get('/pois', {
    params: { city_id: cityId, ...options },
  });
  return response.data;
}

export async function getPOI(poiId: string, lang: 'en' | 'es' = 'en'): Promise<POIDetail> {
  const response = await api.get(`/pois/${poiId}`, { params: { lang } });
  return response.data;
}

export async function searchPOIs(
  query: string,
  cityId?: string,
  limit = 10
): Promise<SearchResponse<POI>> {
  const response = await api.get('/pois/search', {
    params: { q: query, city_id: cityId, limit },
  });
  return response.data;
}

export async function getNearbyPOIs(
  lat: number,
  lng: number,
  radius = 1000,
  limit = 20
): Promise<SearchResponse<POI & { distance_meters: number }>> {
  const response = await api.get('/pois/nearby', {
    params: { lat, lng, radius, limit },
  });
  return response.data;
}

export default api;
