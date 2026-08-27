import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '@/api/client';

export function ReviewPage() {
  const { t } = useTranslation();
  const [reviews, setReviews] = useState<Array<{ id: string; period_type: string; summary: string }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.reviews()
      .then(setReviews)
      .catch(() => setReviews([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500">{t('common.loading')}</p>;

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-6 text-2xl font-bold">{t('review.title')}</h1>
      {reviews.length === 0 ? (
        <p className="text-gray-500">{t('common.noData')}</p>
      ) : (
        <div className="space-y-3">
          {reviews.map((r) => (
            <div key={r.id} className="card">
              <span className="mb-2 inline-block rounded bg-accent-muted px-2 py-0.5 text-xs text-accent">{r.period_type}</span>
              <p className="text-sm">{r.summary}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
