import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { Language } from '@travelers/shared';

interface SettingsState {
  language: Language | null;
  setLanguage: (lang: Language) => void;
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      language: null,
      setLanguage: (language) => set({ language }),
      theme: 'system',
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: 'travelers-settings',
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);
