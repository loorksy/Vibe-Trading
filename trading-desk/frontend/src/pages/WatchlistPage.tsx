import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '@/api/client';
import { useUiStore } from '@/stores/uiStore';
import type { WatchlistItem } from '@/types';

export function WatchlistPage() {
  const { t } = useTranslation();
  const openModal = useUiStore((s) => s.openModal);
  const setSelectedSymbol = useUiStore((s) => s.setSelectedSymbol);
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api.watchlist()
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleAdd = () => {
    openModal('symbolPicker', {
      onSelect: async (id: string) => {
        await api.addWatchlist(id);
        load();
      },
    });
  };

  const handleRemove = async (canonicalId: string) => {
    await api.removeWatchlist(canonicalId);
    load();
  };

  if (loading) return <p className="text-gray-500">{t('common.loading')}</p>;

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t('watchlist.title')}</h1>
        <button onClick={handleAdd} className="btn-primary">{t('watchlist.add')}</button>
      </div>

      {items.length === 0 ? (
        <p className="text-gray-500">{t('common.noData')}</p>
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <div key={item.canonical_id} className="card flex items-center justify-between">
              <button
                onClick={() => setSelectedSymbol(item.canonical_id)}
                className="flex items-center gap-4 text-start"
              >
                <span className="font-mono text-lg font-medium">{item.canonical_id.replace('_', '/')}</span>
                {item.price && (
                  <span className="font-mono text-accent">{item.price.mid?.toFixed(5)}</span>
                )}
              </button>
              <button onClick={() => handleRemove(item.canonical_id)} className="btn-ghost text-sm text-danger">
                {t('watchlist.remove')}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
