import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal } from '@/components/common/Modal';
import { api } from '@/api/client';
import { useUiStore } from '@/stores/uiStore';

export function ConnectBrokerModal() {
  const { t } = useTranslation();
  const { activeModal, closeModal } = useUiStore();
  const [form, setForm] = useState({
    name: '',
    account_type: 'demo',
    metaapi_account_id: '',
    broker_server: '',
    token: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await api.connectBroker(form);
      closeModal();
      setForm({ name: '', account_type: 'demo', metaapi_account_id: '', broker_server: '', token: '' });
    } catch (err) {
      setError(err instanceof Error ? err.message : t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open={activeModal === 'connectBroker'}
      onClose={closeModal}
      title={t('modals.connectBroker.title')}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && <p className="text-sm text-danger">{error}</p>}
        <div>
          <label className="mb-1 block text-sm text-gray-400">{t('modals.connectBroker.name')}</label>
          <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-400">{t('modals.connectBroker.accountType')}</label>
          <select className="input" value={form.account_type} onChange={(e) => setForm({ ...form, account_type: e.target.value })}>
            <option value="demo">Demo</option>
            <option value="live">Live</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-400">{t('modals.connectBroker.metaapiId')}</label>
          <input className="input" value={form.metaapi_account_id} onChange={(e) => setForm({ ...form, metaapi_account_id: e.target.value })} required />
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-400">{t('modals.connectBroker.brokerServer')}</label>
          <input className="input" value={form.broker_server} onChange={(e) => setForm({ ...form, broker_server: e.target.value })} required />
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-400">{t('modals.connectBroker.token')}</label>
          <input className="input" type="password" value={form.token} onChange={(e) => setForm({ ...form, token: e.target.value })} required />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={closeModal} className="btn-secondary">{t('common.cancel')}</button>
          <button type="submit" disabled={loading} className="btn-primary">{loading ? t('common.loading') : t('modals.connectBroker.connect')}</button>
        </div>
      </form>
    </Modal>
  );
}
