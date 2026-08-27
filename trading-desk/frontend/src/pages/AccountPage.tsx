import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '@/api/client';
import { useUiStore } from '@/stores/uiStore';
import type { BrokerAccount } from '@/types';

export function AccountPage() {
  const { t } = useTranslation();
  const openModal = useUiStore((s) => s.openModal);
  const [accounts, setAccounts] = useState<BrokerAccount[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api.accounts()
      .then(setAccounts)
      .catch(() => setAccounts([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t('account.title')}</h1>
        <button onClick={() => openModal('connectBroker')} className="btn-primary">
          {t('account.connect')}
        </button>
      </div>

      <h2 className="mb-3 text-lg font-semibold">{t('account.accounts')}</h2>
      {loading ? (
        <p className="text-gray-500">{t('common.loading')}</p>
      ) : accounts.length === 0 ? (
        <p className="text-gray-500">{t('common.noData')}</p>
      ) : (
        <div className="space-y-3">
          {accounts.map((acc) => (
            <div key={acc.id} className="card flex items-center justify-between">
              <div>
                <p className="font-medium">{acc.name}</p>
                <p className="text-sm text-gray-500">{acc.broker_server} · {acc.account_type}</p>
              </div>
              <span className={`rounded-full px-2 py-1 text-xs ${acc.is_connected ? 'bg-success/20 text-success' : 'bg-gray-700 text-gray-400'}`}>
                {acc.is_connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
