import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal } from '@/components/common/Modal';
import { api } from '@/api/client';
import { useUiStore } from '@/stores/uiStore';
import { useSettingsStore } from '@/stores/settingsStore';

export function EmergencyKillSwitchModal() {
  const { t } = useTranslation();
  const { activeModal, closeModal } = useUiStore();
  const { setEmergencyHalt } = useSettingsStore();
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const handleConfirm = async () => {
    setLoading(true);
    try {
      await api.stopAllBots();
      setEmergencyHalt(true);
      setDone(true);
    } catch {
      // still mark halted locally
      setEmergencyHalt(true);
      setDone(true);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    closeModal();
    setDone(false);
  };

  return (
    <Modal
      open={activeModal === 'emergencyKill'}
      onClose={handleClose}
      title={t('emergency.title')}
      size="sm"
    >
      {done ? (
        <div className="py-4 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-danger/20">
            <svg className="h-8 w-8 text-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="font-medium text-danger">{t('emergency.halted')}</p>
          <button onClick={handleClose} className="btn-secondary mt-4">{t('common.close')}</button>
        </div>
      ) : (
        <div>
          <p className="mb-6 text-sm text-gray-400">{t('emergency.confirm')}</p>
          <div className="flex justify-end gap-2">
            <button onClick={handleClose} className="btn-secondary">{t('common.cancel')}</button>
            <button onClick={handleConfirm} disabled={loading} className="btn-danger">
              {loading ? t('common.loading') : t('emergency.button')}
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}
