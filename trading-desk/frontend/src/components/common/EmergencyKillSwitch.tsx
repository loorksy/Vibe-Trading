import { useTranslation } from 'react-i18next';
import { useUiStore } from '@/stores/uiStore';

export function EmergencyKillSwitch() {
  const { t } = useTranslation();
  const openModal = useUiStore((s) => s.openModal);

  return (
    <button
      onClick={() => openModal('emergencyKill')}
      className="fixed bottom-20 end-4 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-danger text-xs font-bold text-white shadow-lg shadow-danger/30 transition-transform hover:scale-105 hover:bg-danger-hover md:bottom-6"
      title={t('emergency.title')}
      aria-label={t('emergency.title')}
    >
      {t('emergency.button')}
    </button>
  );
}
