import { en } from './en';
import { es } from './es';
import type { Language } from '../types';

export const translations = { en, es } as const;

export type TranslationKey = keyof typeof en;

/**
 * Get a translated string for the given key and language.
 * Falls back to English if the key is not found in the target language.
 */
export function t(
  key: TranslationKey,
  lang: Language = 'en',
  params?: Record<string, string | number>
): string {
  let result: string = translations[lang][key] ?? translations.en[key] ?? key;

  if (params) {
    for (const [k, v] of Object.entries(params)) {
      result = result.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v));
    }
  }

  return result;
}

export { en, es };
