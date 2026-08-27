import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '@/api/client';

export function ExposurePage() {
  const { t } = useTranslation();
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.exposure()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500">{t('common.loading')}</p>;

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-6 text-2xl font-bold">{t('exposure.title')}</h1>
      {!data ? (
        <p className="text-gray-500">{t('common.noData')}</p>
      ) : (
        <div className="card">
          <pre className="overflow-x-auto text-sm text-gray-300">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
