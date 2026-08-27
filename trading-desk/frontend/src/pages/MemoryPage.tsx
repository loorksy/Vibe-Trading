import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '@/api/client';

export function MemoryPage() {
  const { t } = useTranslation();
  const [lessons, setLessons] = useState<Array<{ id: string; lesson: string; canonical_id: string }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.memoryLessons()
      .then(setLessons)
      .catch(() => setLessons([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500">{t('common.loading')}</p>;

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-6 text-2xl font-bold">{t('memory.title')}</h1>
      {lessons.length === 0 ? (
        <p className="text-gray-500">{t('common.noData')}</p>
      ) : (
        <div className="space-y-3">
          {lessons.map((l) => (
            <div key={l.id} className="card">
              <span className="mb-1 inline-block font-mono text-xs text-accent">{l.canonical_id.replace('_', '/')}</span>
              <p className="text-sm">{l.lesson}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
