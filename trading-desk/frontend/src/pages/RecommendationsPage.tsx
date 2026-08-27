import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '@/api/client';
import type { Recommendation } from '@/types';

export function RecommendationsPage() {
  const { t } = useTranslation();
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.recommendations()
      .then(setRecs)
      .catch(() => setRecs([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500">{t('common.loading')}</p>;

  return (
    <div className="mx-auto max-w-6xl">
      <h1 className="mb-6 text-2xl font-bold">{t('recommendations.title')}</h1>
      {recs.length === 0 ? (
        <p className="text-gray-500">{t('common.noData')}</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {recs.map((rec) => (
            <Link key={rec.id} to={`/recommendations/${rec.id}`} className="card hover:border-accent/50 transition-colors">
              <div className="mb-2 flex items-center justify-between">
                <span className="font-mono font-medium">{rec.canonical_id.replace('_', '/')}</span>
                <span className={`rounded px-2 py-0.5 text-xs font-medium ${rec.direction === 'BUY' ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger'}`}>
                  {rec.direction}
                </span>
              </div>
              <p className="text-sm text-gray-400">{rec.timeframe} · {rec.confidence_label}</p>
              <p className="mt-2 text-xs text-gray-500">{rec.execution_status}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
