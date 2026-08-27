import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '@/api/client';
import type { Bot } from '@/types';

export function BotDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams();
  const [bot, setBot] = useState<Bot | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.bots()
      .then((bots) => setBot(bots.find((b) => b.id === id) || null))
      .catch(() => setBot(null))
      .finally(() => setLoading(false));
  }, [id]);

  const handleStop = async () => {
    if (!id) return;
    await api.stopBot(id);
    setBot((b) => b ? { ...b, is_running: false } : null);
  };

  if (loading) return <p className="text-gray-500">{t('common.loading')}</p>;
  if (!bot) return <p className="text-gray-500">{t('common.noData')}</p>;

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-2 text-2xl font-bold">{bot.name}</h1>
      <p className="mb-6 text-gray-500">{bot.canonical_id.replace('_', '/')} · {bot.timeframe} · {bot.state}</p>

      <div className="card mb-4 space-y-3">
        <div className="flex items-center justify-between">
          <span>Status</span>
          <span className={bot.is_running ? 'text-success' : 'text-gray-500'}>
            {bot.is_running ? t('bots.running') : t('bots.stopped')}
          </span>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {bot.is_running && (
          <button onClick={handleStop} className="btn-danger">{t('bots.stop')}</button>
        )}
        {bot.state === 'demo' && (
          <Link to={`/bots/${id}/live`} className="btn-primary">{t('bots.promoteLive')}</Link>
        )}
      </div>
    </div>
  );
}
