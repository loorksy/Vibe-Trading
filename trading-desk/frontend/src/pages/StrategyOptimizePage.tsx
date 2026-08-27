import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { SymbolPicker } from '@/components/SymbolPicker';
import { useUiStore } from '@/stores/uiStore';

export function StrategyOptimizePage() {
  const { t } = useTranslation();
  const { id } = useParams();
  const selectedSymbol = useUiStore((s) => s.selectedSymbol);
  const [timeframe, setTimeframe] = useState('1h');
  const [results, setResults] = useState<string | null>(null);

  const handleOptimize = () => {
    setResults(`Optimization queued for strategy ${id} on ${selectedSymbol} (${timeframe})`);
  };

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-6 text-2xl font-bold">{t('strategies.optimize')}</h1>
      <div className="card space-y-4">
        <p className="text-sm text-gray-500">Strategy ID: {id}</p>
        <div className="flex flex-wrap gap-3">
          <SymbolPicker />
          <select className="input w-auto" value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
            {['15m', '1h', '4h', '1d'].map((tf) => <option key={tf} value={tf}>{tf}</option>)}
          </select>
        </div>
        <button onClick={handleOptimize} className="btn-primary">{t('strategies.optimize')}</button>
        {results && <p className="text-sm text-accent">{results}</p>}
      </div>
    </div>
  );
}
