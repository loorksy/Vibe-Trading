import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal } from '@/components/common/Modal';
import { api } from '@/api/client';
import { useUiStore } from '@/stores/uiStore';
import type { BrokerAccount } from '@/types';

export function ExecuteTradeModal() {
  const { t } = useTranslation();
  const { activeModal, closeModal, modalData } = useUiStore();
  const [accounts, setAccounts] = useState<BrokerAccount[]>([]);
  const [accountId, setAccountId] = useState('');
  const [lotSize, setLotSize] = useState('0.01');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const recommendationId = modalData.recommendationId as string | undefined;

  useEffect(() => {
    if (activeModal === 'executeTrade') {
      api.accounts().then(setAccounts).catch(() => setAccounts([]));
      setSuccess(false);
      setError('');
    }
  }, [activeModal]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!recommendationId) return;
    setLoading(true);
    setError('');
    try {
      await api.executeTrade({
        recommendation_id: recommendationId,
        account_id: accountId,
        lot_size: parseFloat(lotSize),
      });
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open={activeModal === 'executeTrade'}
      onClose={closeModal}
      title={t('modals.executeTrade.title')}
    >
      {success ? (
        <div className="py-4 text-center">
          <p className="text-success">Order submitted successfully</p>
          <button onClick={closeModal} className="btn-primary mt-4">{t('common.close')}</button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <p className="text-sm text-danger">{error}</p>}
          <div>
            <label className="mb-1 block text-sm text-gray-400">{t('modals.executeTrade.account')}</label>
            <select className="input" value={accountId} onChange={(e) => setAccountId(e.target.value)} required>
              <option value="">—</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>{a.name} ({a.account_type})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm text-gray-400">{t('modals.executeTrade.lotSize')}</label>
            <input className="input" type="number" step="0.01" min="0.01" value={lotSize} onChange={(e) => setLotSize(e.target.value)} required />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={closeModal} className="btn-secondary">{t('common.cancel')}</button>
            <button type="submit" disabled={loading || !accountId} className="btn-primary">
              {loading ? t('common.loading') : t('modals.executeTrade.execute')}
            </button>
          </div>
        </form>
      )}
    </Modal>
  );
}
