import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '@/api/client';
import type { Bot } from '@/types';

export function BotsPage() {
  const { t } = useTranslation();
  const [bots, setBots] = useState<Bot[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.bots()
      .then(setBots)
      .catch(() => setBots([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500">{t('common.loading')}</p>;

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-6 text-2xl font-bold">{t('bots.title')}</h1>
      {bots.length === 0 ? (
        <p className="text-gray-500">{t('common.noData')}</p>
      ) : (
        <div className="space-y-3">
          {bots.map((bot) => (
            <Link key={bot.id} to={`/bots/${bot.id}`} className="card flex items-center justify-between hover:border-accent/50">
              <div>
                <p className="font-medium">{bot.name}</p>
                <p className="text-sm text-gray-500">{bot.canonical_id.replace('_', '/')} · {bot.timeframe}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`rounded px-2 py-0.5 text-xs ${bot.is_running ? 'bg-success/20 text-success' : 'bg-gray-700 text-gray-400'}`}>
                  {bot.is_running ? t('bots.running') : t('bots.stopped')}
                </span>
                <span className="text-xs text-gray-500">{bot.state}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
