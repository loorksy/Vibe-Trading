import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '@/api/client';
import { useUiStore } from '@/stores/uiStore';
import type { Recommendation } from '@/types';

export function RecommendationDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams();
  const openModal = useUiStore((s) => s.openModal);
  const [rec, setRec] = useState<Recommendation | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    api.recommendation(id)
      .then(setRec)
      .catch(() => setRec(null))
      .finally(() => setLoading(false));
  }, [id]);

  const handleConvertBot = async () => {
    if (!id) return;
    try {
      const res = await api.convertToBot(id);
      window.location.href = `/bots/${res.bot_id}`;
    } catch {
      // ignore
    }
  };

  if (loading) return <p className="text-gray-500">{t('common.loading')}</p>;
  if (!rec) return <p className="text-gray-500">{t('common.noData')}</p>;

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold font-mono">{rec.canonical_id.replace('_', '/')}</h1>
          <p className="text-gray-500">{rec.timeframe} · {rec.analysis_mode}</p>
        </div>
        <span className={`rounded-lg px-3 py-1 text-sm font-bold ${rec.direction === 'BUY' ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger'}`}>
          {rec.direction}
        </span>
      </div>

      <div className="card mb-4 space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-xs text-gray-500">{t('recommendations.entry')}</p>
            <p className="font-mono">{rec.entry_zone_low} – {rec.entry_zone_high}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">{t('recommendations.stop')}</p>
            <p className="font-mono text-danger">{rec.stop_loss}</p>
          </div>
        </div>
        <div>
          <p className="text-xs text-gray-500">{t('recommendations.targets')}</p>
          <div className="mt-1 flex flex-wrap gap-2">
            {rec.take_profits.map((tp, i) => (
              <span key={i} className="rounded bg-success/10 px-2 py-1 font-mono text-sm text-success">
                {tp.price}
              </span>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs text-gray-500">{t('recommendations.confidence')}</p>
          <p>{rec.confidence_label}</p>
        </div>
        <p className="text-sm text-gray-400">{rec.invalidation_rule}</p>
      </div>

      <div className="flex flex-wrap gap-2">
        <button onClick={() => openModal('executeTrade', { recommendationId: rec.id })} className="btn-primary">
          {t('recommendations.execute')}
        </button>
        <button onClick={handleConvertBot} className="btn-secondary">
          {t('recommendations.convertBot')}
        </button>
      </div>
    </div>
  );
}
