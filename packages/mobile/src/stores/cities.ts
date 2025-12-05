import { create } from 'zustand';
import type { City } from '@travelers/shared';
import { searchCities, getCity } from '../api/client';

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

export const useCitiesStore = create<CitiesState>((set, get) => ({
  searchResults: [],
  searchQuery: '',
  isSearching: false,
  selectedCity: null,
  recentCities: [],

  search: async (query: string) => {
    set({ searchQuery: query, isSearching: true });

    if (query.length < 2) {
      set({ searchResults: [], isSearching: false });
      return;
    }

    try {
      const response = await searchCities(query);
      set({ searchResults: response.items, isSearching: false });
    } catch (error) {
      console.error('City search error:', error);
      set({ searchResults: [], isSearching: false });
    }
  },

  selectCity: async (cityId: string) => {
    try {
      const city = await getCity(cityId);
      const recentCities = get().recentCities.filter((c) => c.id !== cityId);
      set({
        selectedCity: city,
        recentCities: [city, ...recentCities].slice(0, 5),
      });
    } catch (error) {
      console.error('Get city error:', error);
    }
  },

  clearSearch: () => {
    set({ searchQuery: '', searchResults: [] });
  },
}));
