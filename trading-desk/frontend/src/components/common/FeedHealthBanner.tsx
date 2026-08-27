import { useTranslation } from 'react-i18next';
import { useSettingsStore } from '@/stores/settingsStore';

export function FeedHealthBanner() {
  const { t } = useTranslation();
  const { feedHealth, emergencyHalt } = useSettingsStore();

  if (emergencyHalt) {
    return (
      <div className="bg-danger px-4 py-2 text-center text-sm font-medium text-white">
        {t('emergency.halted')}
      </div>
    );
  }

  if (!feedHealth || feedHealth.healthy !== false) return null;

  return (
    <div className="bg-warning/20 border-b border-warning/40 px-4 py-2 text-center text-sm text-warning">
      <span className="inline-flex items-center gap-2">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        {t('feedHealth.unreliable')}
      </span>
    </div>
  );
}
