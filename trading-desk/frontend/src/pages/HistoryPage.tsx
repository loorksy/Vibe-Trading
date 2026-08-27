import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '@/api/client';
import type { Execution } from '@/types';

export function HistoryPage() {
  const { t } = useTranslation();
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.executions()
      .then(setExecutions)
      .catch(() => setExecutions([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500">{t('common.loading')}</p>;

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-6 text-2xl font-bold">{t('history.title')}</h1>
      {executions.length === 0 ? (
        <p className="text-gray-500">{t('common.noData')}</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700 text-start text-gray-500">
                <th className="pb-2 pe-4">Symbol</th>
                <th className="pb-2 pe-4">Direction</th>
                <th className="pb-2 pe-4">Lots</th>
                <th className="pb-2 pe-4">Status</th>
                <th className="pb-2">Date</th>
              </tr>
            </thead>
            <tbody>
              {executions.map((e) => (
                <tr key={e.id} className="border-b border-gray-800">
                  <td className="py-3 pe-4 font-mono">{e.canonical_id.replace('_', '/')}</td>
                  <td className={`py-3 pe-4 ${e.direction === 'BUY' ? 'text-success' : 'text-danger'}`}>{e.direction}</td>
                  <td className="py-3 pe-4">{e.lot_size}</td>
                  <td className="py-3 pe-4">
                    <span className="rounded bg-surface-overlay px-2 py-0.5 text-xs">{e.status}</span>
                    {e.is_demo && <span className="ms-1 text-xs text-gray-500">demo</span>}
                  </td>
                  <td className="py-3 text-gray-500">{new Date(e.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
