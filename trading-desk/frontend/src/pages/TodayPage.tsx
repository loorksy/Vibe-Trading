import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '@/api/client';
import { useUiStore } from '@/stores/uiStore';
import { SymbolPicker } from '@/components/SymbolPicker';
import { useSettingsStore } from '@/stores/settingsStore';

import type { FeedHealth } from '@/types';

export function TodayPage() {
  const { t } = useTranslation();
  const selectedSymbol = useUiStore((s) => s.selectedSymbol);
  const setFeedHealth = useSettingsStore((s) => s.setFeedHealth);
  const [data, setData] = useState<{
    news: Array<Record<string, unknown>>;
    calendar: Array<Record<string, unknown>>;
    feed_health: FeedHealth;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.today(selectedSymbol)
      .then((res) => {
        setData(res);
        setFeedHealth(res.feed_health as import('@/types').FeedHealth);
      })
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [selectedSymbol, setFeedHealth]);

  if (loading) return <p className="text-gray-500">{t('common.loading')}</p>;

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">{t('today.title')}</h1>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">{t('today.benchmark')}:</span>
          <SymbolPicker />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">{t('today.news')}</h2>
          {!data?.news?.length ? (
            <p className="text-gray-500">{t('common.noData')}</p>
          ) : (
            <ul className="space-y-3">
              {data.news.map((item, i) => (
                <li key={i} className="border-b border-gray-700/50 pb-3 last:border-0">
                  <p className="text-sm font-medium">{(item.headline as string) || (item.title as string) || 'News item'}</p>
                  {item.summary != null && <p className="mt-1 text-xs text-gray-500">{String(item.summary)}</p>}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">{t('today.calendar')}</h2>
          {!data?.calendar?.length ? (
            <p className="text-gray-500">{t('common.noData')}</p>
          ) : (
            <ul className="space-y-3">
              {data.calendar.map((item, i) => (
                <li key={i} className="flex items-start justify-between border-b border-gray-700/50 pb-3 last:border-0">
                  <div>
                    <p className="text-sm font-medium">{(item.event as string) || (item.title as string) || 'Event'}</p>
                    <p className="text-xs text-gray-500">{String(item.country || '')}</p>
                  </div>
                  <span className="text-xs text-accent">{String(item.impact || item.time || '')}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
