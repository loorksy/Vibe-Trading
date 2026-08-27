import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '@/api/client';
import type { Candle } from '@/types';

interface ChartPanelProps {
  canonicalId: string;
  timeframe?: string;
  height?: number;
}

export function ChartPanel({ canonicalId, timeframe = '1h', height = 400 }: ChartPanelProps) {
  const { t } = useTranslation();
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<unknown>(null);

  useEffect(() => {
    let cancelled = false;

    async function initChart() {
      if (!containerRef.current) return;

      try {
        const { candles } = await api.candles(canonicalId, timeframe, 200);
        if (cancelled || !containerRef.current) return;

        // @klinecharts/pro placeholder — render simple candlestick summary
        // Full klinecharts integration requires license setup
        containerRef.current.innerHTML = '';
        const canvas = document.createElement('canvas');
        canvas.width = containerRef.current.clientWidth;
        canvas.height = height;
        containerRef.current.appendChild(canvas);

        const ctx = canvas.getContext('2d');
        if (!ctx || !candles.length) return;

        drawCandles(ctx, candles, canvas.width, canvas.height);
        chartRef.current = canvas;
      } catch {
        if (containerRef.current) {
          containerRef.current.innerHTML = `<p class="flex h-full items-center justify-center text-gray-500">${t('chart.placeholder')}</p>`;
        }
      }
    }

    initChart();
    return () => {
      cancelled = true;
    };
  }, [canonicalId, timeframe, height, t]);

  return (
    <div className="card overflow-hidden p-0">
      <div className="flex items-center justify-between border-b border-gray-700 px-4 py-2">
        <span className="font-mono text-sm font-medium">{canonicalId.replace('_', '/')}</span>
        <span className="text-xs text-gray-500">{timeframe}</span>
      </div>
      <div ref={containerRef} style={{ height }} className="w-full" />
    </div>
  );
}

function drawCandles(
  ctx: CanvasRenderingContext2D,
  candles: Candle[],
  width: number,
  height: number,
) {
  const padding = 40;
  const chartW = width - padding * 2;
  const chartH = height - padding * 2;

  const highs = candles.map((c) => c.high);
  const lows = candles.map((c) => c.low);
  const maxPrice = Math.max(...highs);
  const minPrice = Math.min(...lows);
  const range = maxPrice - minPrice || 1;

  const barWidth = Math.max(2, chartW / candles.length - 1);

  ctx.fillStyle = '#0f1419';
  ctx.fillRect(0, 0, width, height);

  // Grid
  ctx.strokeStyle = '#1a2332';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = padding + (chartH / 4) * i;
    ctx.beginPath();
    ctx.moveTo(padding, y);
    ctx.lineTo(width - padding, y);
    ctx.stroke();
  }

  candles.forEach((candle, i) => {
    const x = padding + (i / candles.length) * chartW;
    const yHigh = padding + ((maxPrice - candle.high) / range) * chartH;
    const yLow = padding + ((maxPrice - candle.low) / range) * chartH;
    const yOpen = padding + ((maxPrice - candle.open) / range) * chartH;
    const yClose = padding + ((maxPrice - candle.close) / range) * chartH;

    const bullish = candle.close >= candle.open;
    ctx.strokeStyle = bullish ? '#22c55e' : '#ef4444';
    ctx.fillStyle = bullish ? '#22c55e' : '#ef4444';

    // Wick
    ctx.beginPath();
    ctx.moveTo(x + barWidth / 2, yHigh);
    ctx.lineTo(x + barWidth / 2, yLow);
    ctx.stroke();

    // Body
    const bodyTop = Math.min(yOpen, yClose);
    const bodyH = Math.max(1, Math.abs(yClose - yOpen));
    ctx.fillRect(x, bodyTop, barWidth, bodyH);
  });
}
