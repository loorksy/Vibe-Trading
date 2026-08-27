import { useEffect, useRef } from 'react';
import { KLineChartPro } from '@klinecharts/pro';
import '@klinecharts/pro/dist/klinecharts-pro.css';
import { OandaDatafeed, timeframeToPeriod } from '@/lib/oandaDatafeed';
import type { Instrument } from '@/types';

interface KLineChartPanelProps {
  canonicalId: string;
  timeframe?: string;
  height?: number;
  instruments?: Instrument[];
  overlays?: Array<{
    type: 'entry' | 'stop_loss' | 'take_profit' | 'support' | 'resistance';
    price: number;
    label?: string;
  }>;
}

export function KLineChartPanel({
  canonicalId,
  timeframe = '1h',
  height = 400,
  instruments = [],
  overlays = [],
}: KLineChartPanelProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<KLineChartPro | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const datafeed = new OandaDatafeed(instruments);
    const period = timeframeToPeriod(timeframe);

    const chart = new KLineChartPro({
      container: containerRef.current,
      theme: 'dark',
      drawingBarVisible: true,
      symbol: {
        ticker: canonicalId,
        name: canonicalId.replace('_', ''),
        pricePrecision: canonicalId.includes('JPY') ? 3 : 5,
      },
      period,
      periods: [
        timeframeToPeriod('15m'),
        timeframeToPeriod('1h'),
        timeframeToPeriod('4h'),
        timeframeToPeriod('1d'),
      ],
      mainIndicators: [],
      subIndicators: [],
      datafeed,
    });

    chartRef.current = chart;

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
      chartRef.current = null;
    };
  }, [canonicalId, timeframe, instruments]);

  return (
    <div className="card overflow-hidden p-0">
      <div className="flex items-center justify-between border-b border-gray-700 px-4 py-2">
        <span className="font-mono text-sm font-medium">{canonicalId.replace('_', '/')}</span>
        <span className="text-xs text-gray-500">{timeframe}</span>
      </div>
      <div ref={containerRef} style={{ height }} className="w-full" />
      {overlays.length > 0 && (
        <div className="flex flex-wrap gap-2 border-t border-gray-700 px-4 py-2">
          {overlays.map((o, i) => (
            <span
              key={i}
              className={`rounded px-2 py-0.5 text-xs ${
                o.type === 'entry' ? 'bg-blue-500/20 text-blue-400' :
                o.type === 'stop_loss' ? 'bg-red-500/20 text-red-400' :
                o.type === 'take_profit' ? 'bg-green-500/20 text-green-400' :
                'bg-gray-500/20 text-gray-400'
              }`}
            >
              {o.label ?? o.type}: {o.price}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
