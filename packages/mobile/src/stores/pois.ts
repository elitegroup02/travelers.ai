import { create } from 'zustand';
import type { POI, POIDetail } from '@travelers/shared';
import { getPOIsForCity, getPOI, searchPOIs } from '../api/client';

interface POIsState {
  pois: POI[];
  selectedPOI: POIDetail | null;
  isLoading: boolean;
  hasMore: boolean;
  total: number;

  loadPOIsForCity: (cityId: string, options?: { poiType?: string; reset?: boolean }) => Promise<void>;
  loadMorePOIs: (cityId: string, poiType?: string) => Promise<void>;
  selectPOI: (poiId: string, language: 'en' | 'es') => Promise<void>;
  searchPOIs: (query: string, cityId?: string) => Promise<void>;
  clearSelection: () => void;
}

export const usePOIsStore = create<POIsState>((set, get) => ({
  pois: [],
  selectedPOI: null,
  isLoading: false,
  hasMore: false,
  total: 0,

  loadPOIsForCity: async (cityId, options = {}) => {
    const { poiType, reset = true } = options;

    if (reset) {
      set({ pois: [], isLoading: true });
    }

    try {
      const response = await getPOIsForCity(cityId, { poiType, limit: 20, offset: 0 });
      set({
        pois: response.items,
        hasMore: response.has_more,
        total: response.total,
        isLoading: false,
      });
    } catch (error) {
      console.error('Load POIs error:', error);
      set({ isLoading: false });
    }
  },

  loadMorePOIs: async (cityId, poiType) => {
    const { pois, isLoading, hasMore } = get();

    if (isLoading || !hasMore) return;

    set({ isLoading: true });

    try {
      const response = await getPOIsForCity(cityId, {
        poiType,
        limit: 20,
        offset: pois.length,
      });
      set({
        pois: [...pois, ...response.items],
        hasMore: response.has_more,
        isLoading: false,
      });
    } catch (error) {
      console.error('Load more POIs error:', error);
      set({ isLoading: false });
    }
  },

  selectPOI: async (poiId, language) => {
    set({ isLoading: true });

    try {
      const poi = await getPOI(poiId, language);
      set({ selectedPOI: poi, isLoading: false });
    } catch (error) {
      console.error('Get POI error:', error);
      set({ isLoading: false });
    }
  },

  searchPOIs: async (query, cityId) => {
    if (query.length < 2) {
      return;
    }

    set({ isLoading: true });

    try {
      const response = await searchPOIs(query, cityId);
      set({ pois: response.items, total: response.total, isLoading: false });
    } catch (error) {
      console.error('Search POIs error:', error);
      set({ isLoading: false });
    }
  },

  clearSelection: () => {
    set({ selectedPOI: null });
  },
}));
