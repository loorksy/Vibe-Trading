import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { FeedHealth, OperatorSettings } from '@/types';
import { api } from '@/api/client';

interface SettingsState {
  theme: 'dark' | 'light';
  language: string;
  settings: OperatorSettings | null;
  feedHealth: FeedHealth | null;
  emergencyHalt: boolean;
  setTheme: (theme: 'dark' | 'light') => void;
  setLanguage: (lang: string) => void;
  loadSettings: () => Promise<void>;
  updateSettings: (partial: Partial<OperatorSettings>) => Promise<void>;
  setFeedHealth: (health: FeedHealth | null) => void;
  setEmergencyHalt: (halt: boolean) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      theme: 'dark',
      language: 'en',
      settings: null,
      feedHealth: null,
      emergencyHalt: false,

      setTheme: (theme) => {
        document.documentElement.classList.toggle('dark', theme === 'dark');
        document.documentElement.classList.toggle('light', theme === 'light');
        set({ theme });
        get().updateSettings({ theme }).catch(() => {});
      },

      setLanguage: (language) => {
        set({ language });
        document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
        document.documentElement.lang = language;
        get().updateSettings({ language }).catch(() => {});
      },

      loadSettings: async () => {
        try {
          const settings = await api.settings();
          set({
            settings,
            emergencyHalt: settings.emergency_halt,
            feedHealth: settings.feed_health as FeedHealth,
            theme: (settings.theme as 'dark' | 'light') || 'dark',
            language: settings.language || 'en',
          });
          document.documentElement.classList.toggle('dark', settings.theme === 'dark');
          document.documentElement.dir = settings.language === 'ar' ? 'rtl' : 'ltr';
        } catch {
          // Not logged in yet
        }
      },

      updateSettings: async (partial) => {
        await api.updateSettings(partial);
        const settings = await api.settings();
        set({ settings });
      },

      setFeedHealth: (feedHealth) => set({ feedHealth }),
      setEmergencyHalt: (emergencyHalt) => set({ emergencyHalt }),
    }),
    {
      name: 'trading-desk-settings',
      partialize: (s) => ({ theme: s.theme, language: s.language }),
    },
  ),
);
