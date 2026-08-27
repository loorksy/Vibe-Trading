import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import type { Recommendation } from '@/types';

interface RecommendationCardProps {
  data: Recommendation & { id: string };
  compact?: boolean;
}

export function RecommendationCard({ data, compact = false }: RecommendationCardProps) {
  const { t } = useTranslation();
  const isBuy = data.direction === 'BUY';
  const gateResults = Array.isArray(data.gate_results)
    ? data.gate_results
    : Object.values(data.gate_results ?? {});

  if (compact) {
    return (
      <Link
        to={`/recommendations/${data.id}`}
        className="mt-2 block rounded-lg border border-accent/30 bg-accent-muted p-3 text-sm hover:border-accent transition-colors"
      >
        <div className="flex items-center justify-between">
          <span className={`font-bold ${isBuy ? 'text-green-400' : 'text-red-400'}`}>
            {data.direction} {data.canonical_id?.replace('_', '')}
          </span>
          <span className="text-xs text-gray-500">{data.analysis_mode === 'deep_analysis' ? 'Deep' : 'Quick'}</span>
        </div>
        <p className="mt-1 text-xs text-gray-400">
          Entry: {data.preferred_entry} · SL: {data.stop_loss}
        </p>
      </Link>
    );
  }

  return (
    <div className="mt-3 rounded-xl border border-gray-700 bg-surface-overlay p-4">
      <div className="flex items-start justify-between">
        <div>
          <span className={`text-lg font-bold ${isBuy ? 'text-green-400' : 'text-red-400'}`}>
            {data.direction}
          </span>
          <span className="ml-2 font-mono text-sm text-gray-300">
            {data.canonical_id?.replace('_', '/')}
          </span>
          <span className="ml-2 rounded bg-gray-700 px-1.5 py-0.5 text-xs">{data.timeframe}</span>
        </div>
        <span className={`rounded px-2 py-0.5 text-xs ${
          data.analysis_mode === 'deep_analysis' ? 'bg-purple-500/20 text-purple-300' : 'bg-gray-600/30 text-gray-400'
        }`}>
          {data.analysis_mode === 'deep_analysis' ? t('ask.deepAnalysis') : t('ask.quickScan')}
        </span>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
        <div>
          <span className="text-gray-500">Entry zone</span>
          <p className="font-mono">{data.entry_zone_low} – {data.entry_zone_high}</p>
        </div>
        <div>
          <span className="text-gray-500">Stop loss</span>
          <p className="font-mono text-red-400">{data.stop_loss}</p>
        </div>
        <div>
          <span className="text-gray-500">Plan</span>
          <p>{data.plan_type} · {data.execution_status}</p>
        </div>
        <div>
          <span className="text-gray-500">Confidence</span>
          <p>{data.confidence_label}</p>
        </div>
      </div>

      {data.take_profits?.length > 0 && (
        <div className="mt-2">
          <span className="text-xs text-gray-500">Take profits</span>
          <div className="flex gap-2 mt-1">
            {data.take_profits.map((tp, i) => (
              <span key={i} className="rounded bg-green-500/10 px-2 py-0.5 text-xs font-mono text-green-400">
                TP{i + 1}: {tp.price}
              </span>
            ))}
          </div>
        </div>
      )}

      {gateResults.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {(gateResults as Array<{ gate?: string; passed?: boolean }>).map((g, i) => (
            <span
              key={i}
              className={`rounded px-1.5 py-0.5 text-xs ${
                g.passed ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
              }`}
              title={g.gate}
            >
              {g.gate?.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      )}

      <Link
        to={`/recommendations/${data.id}`}
        className="mt-3 inline-block text-xs text-accent hover:underline"
      >
        View full details →
      </Link>
    </div>
  );
}
