import { useTranslation } from 'react-i18next';
import i18n from '@/i18n';
import { useSettingsStore } from '@/stores/settingsStore';

const LANGUAGES = [
  { code: 'en', label: 'EN' },
  { code: 'tr', label: 'TR' },
  { code: 'ar', label: 'AR' },
];

export function LanguageSwitcher() {
  const { t } = useTranslation();
  const { language, setLanguage } = useSettingsStore();

  const handleChange = (code: string) => {
    setLanguage(code);
    i18n.changeLanguage(code);
  };

  return (
    <div className="flex items-center gap-1 rounded-lg bg-surface-overlay p-1" title={t('settings.language')}>
      {LANGUAGES.map((lang) => (
        <button
          key={lang.code}
          onClick={() => handleChange(lang.code)}
          className={`rounded-md px-2 py-1 text-xs font-medium transition-colors ${
            language === lang.code
              ? 'bg-accent text-white'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          {lang.label}
        </button>
      ))}
    </div>
  );
}
