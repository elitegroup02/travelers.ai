import { useCallback, useMemo } from 'react';
import { getLocales } from 'expo-localization';
import { translations, t, type TranslationKey, type Language } from '@travelers/shared';
import { useSettingsStore } from '../stores/settings';

export function useI18n() {
  const preferredLanguage = useSettingsStore((state) => state.language);
  const setLanguage = useSettingsStore((state) => state.setLanguage);

  const deviceLanguage = useMemo((): Language => {
    const locales = getLocales();
    const lang = locales[0]?.languageCode;
    return lang === 'es' ? 'es' : 'en';
  }, []);

  const language: Language = preferredLanguage ?? deviceLanguage;

  const translate = useCallback(
    (key: TranslationKey, params?: Record<string, string | number>): string => {
      return t(key, language, params);
    },
    [language]
  );

  return {
    language,
    setLanguage,
    t: translate,
    translations: translations[language],
  };
}
