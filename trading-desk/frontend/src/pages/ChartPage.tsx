import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useUiStore } from '@/stores/uiStore';
import { SymbolPicker } from '@/components/SymbolPicker';
import { ChartPanel } from '@/components/ChartPanel';

const TIMEFRAMES = ['15m', '1h', '4h', '1d'];

export function ChartPage() {
  const { t } = useTranslation();
  const { symbol } = useParams();
  const selectedSymbol = useUiStore((s) => s.selectedSymbol);
  const setSelectedSymbol = useUiStore((s) => s.setSelectedSymbol);
  const [timeframe, setTimeframe] = useState('1h');

  useEffect(() => {
    if (symbol) setSelectedSymbol(symbol);
  }, [symbol, setSelectedSymbol]);

  const canonicalId = symbol || selectedSymbol;

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">{t('chart.title')}</h1>
        <div className="flex items-center gap-2">
          <SymbolPicker value={canonicalId} onChange={setSelectedSymbol} />
          <select className="input w-auto" value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
            {TIMEFRAMES.map((tf) => <option key={tf} value={tf}>{tf}</option>)}
          </select>
        </div>
      </div>
      <ChartPanel canonicalId={canonicalId} timeframe={timeframe} height={500} />
    </div>
  );
}
