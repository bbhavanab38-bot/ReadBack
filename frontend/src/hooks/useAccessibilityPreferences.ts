import { useEffect, useState } from 'react';

export type ReadBackLanguage = 'en' | 'kn' | 'hi' | 'ta';
export type ReadBackFontSize = 'normal' | 'large' | 'xlarge';

export interface AccessibilityPreferences {
  elderMode: boolean;
  caregiverView: boolean;
  simplifiedLanguage: boolean;
  ttsEnabled: boolean;
  highContrast: boolean;
  fontSize: ReadBackFontSize;
  language: ReadBackLanguage;
}

const STORAGE_KEY = 'readback-accessibility-preferences';

const DEFAULT_PREFERENCES: AccessibilityPreferences = {
  elderMode: false,
  caregiverView: false,
  simplifiedLanguage: false,
  ttsEnabled: true,
  highContrast: false,
  fontSize: 'normal',
  language: 'en',
};

function loadPreferences(): AccessibilityPreferences {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) return DEFAULT_PREFERENCES;
    const parsed = JSON.parse(stored) as Partial<AccessibilityPreferences>;
    return {
      ...DEFAULT_PREFERENCES,
      ...parsed,
      fontSize: ['normal', 'large', 'xlarge'].includes(parsed.fontSize || '') ? parsed.fontSize! : 'normal',
      language: ['en', 'kn', 'hi', 'ta'].includes(parsed.language || '') ? parsed.language! : 'en',
    };
  } catch {
    return DEFAULT_PREFERENCES;
  }
}

export function useAccessibilityPreferences() {
  const [preferences, setPreferences] = useState<AccessibilityPreferences>(loadPreferences);

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
    } catch {
      // Preferences remain available for this session when storage is unavailable.
    }
  }, [preferences]);

  return [preferences, setPreferences] as const;
}