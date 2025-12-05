import type { Coordinates, Language } from '../types';

/**
 * Calculate haversine distance between two coordinates in kilometers.
 */
export function haversineDistance(a: Coordinates, b: Coordinates): number {
  const R = 6371;
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const lat1 = toRad(a.lat);
  const lat2 = toRad(b.lat);

  const x =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.sin(dLng / 2) * Math.sin(dLng / 2) * Math.cos(lat1) * Math.cos(lat2);
  const c = 2 * Math.atan2(Math.sqrt(x), Math.sqrt(1 - x));

  return R * c;
}

function toRad(deg: number): number {
  return deg * (Math.PI / 180);
}

/**
 * Estimate walking time in minutes based on distance.
 * Assumes 5 km/h walking speed with 1.3x factor for non-straight routes.
 */
export function estimateWalkingMinutes(distanceKm: number): number {
  const walkingSpeedKmh = 5;
  const routeFactor = 1.3;
  return Math.round((distanceKm * routeFactor) / walkingSpeedKmh * 60);
}

/**
 * Format duration in minutes to human-readable string.
 */
export function formatDuration(minutes: number, lang: Language = 'en'): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;

  if (lang === 'es') {
    if (hours === 0) return `${mins} min`;
    if (mins === 0) return `${hours} h`;
    return `${hours} h ${mins} min`;
  }

  if (hours === 0) return `${mins} min`;
  if (mins === 0) return `${hours}h`;
  return `${hours}h ${mins}min`;
}

/**
 * Format distance in kilometers to human-readable string.
 */
export function formatDistance(km: number): string {
  if (km < 1) {
    const meters = Math.round(km * 1000);
    return `${meters} m`;
  }
  return `${km.toFixed(1)} km`;
}

/**
 * Format a date string for display.
 */
export function formatDate(
  dateStr: string,
  lang: Language = 'en',
  options: Intl.DateTimeFormatOptions = { dateStyle: 'medium' }
): string {
  const date = new Date(dateStr);
  const locale = lang === 'es' ? 'es-ES' : 'en-US';
  return new Intl.DateTimeFormat(locale, options).format(date);
}

/**
 * Format time string (HH:MM) for display.
 */
export function formatTime(timeStr: string, lang: Language = 'en'): string {
  const [hours, minutes] = timeStr.split(':').map(Number);
  const date = new Date();
  date.setHours(hours, minutes);

  const locale = lang === 'es' ? 'es-ES' : 'en-US';
  return new Intl.DateTimeFormat(locale, {
    hour: 'numeric',
    minute: '2-digit',
    hour12: lang === 'en'
  }).format(date);
}

/**
 * Generate a random share token.
 */
export function generateShareToken(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let token = '';
  for (let i = 0; i < 16; i++) {
    token += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return token;
}
