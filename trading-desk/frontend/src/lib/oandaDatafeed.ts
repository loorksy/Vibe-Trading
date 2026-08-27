import type { Candle, Instrument, Period, SymbolInfo } from '@/types';
import type { KLineData } from 'klinecharts';
import type { Datafeed, DatafeedSubscribeCallback } from '@klinecharts/pro';
import { api } from '@/api/client';

const TIMEFRAME_TO_PERIOD: Record<string, Period> = {
  '1m': { multiplier: 1, timespan: 'minute', text: '1m' },
  '5m': { multiplier: 5, timespan: 'minute', text: '5m' },
  '15m': { multiplier: 15, timespan: 'minute', text: '15m' },
  '30m': { multiplier: 30, timespan: 'minute', text: '30m' },
  '1h': { multiplier: 1, timespan: 'hour', text: '1H' },
  '4h': { multiplier: 4, timespan: 'hour', text: '4H' },
  '1d': { multiplier: 1, timespan: 'day', text: 'D' },
};

function toKLineData(candles: Candle[]): KLineData[] {
  return candles.map((c) => ({
    timestamp: new Date(c.time).getTime(),
    open: c.open,
    high: c.high,
    low: c.low,
    close: c.close,
    volume: c.volume ?? 0,
  }));
}

export class OandaDatafeed implements Datafeed {
  constructor(private instruments: Instrument[] = []) {}

  async searchSymbols(search?: string): Promise<SymbolInfo[]> {
    const items = this.instruments.length
      ? this.instruments
      : await api.instruments(search);
    const filtered = search
      ? items.filter(
          (i) =>
            i.display_symbol.toLowerCase().includes(search.toLowerCase()) ||
            i.canonical_id.toLowerCase().includes(search.toLowerCase()),
        )
      : items;
    return filtered.map((i) => ({
      ticker: i.canonical_id,
      name: i.display_symbol,
      shortName: i.display_symbol,
      market: i.asset_class,
      pricePrecision: 5,
      volumePrecision: 0,
    }));
  }

  async getHistoryKLineData(
    symbol: SymbolInfo,
    period: Period,
    _from: number,
    _to: number,
  ): Promise<KLineData[]> {
    const tf = period.text.toLowerCase();
    const { candles } = await api.candles(symbol.ticker, tf === '1h' ? '1h' : tf, 500);
    return toKLineData(candles);
  }

  subscribe(
    _symbol: SymbolInfo,
    _period: Period,
    _callback: DatafeedSubscribeCallback,
  ) {}

  unsubscribe(_symbol: SymbolInfo, _period: Period) {}
}

export function timeframeToPeriod(tf: string): Period {
  return TIMEFRAME_TO_PERIOD[tf] ?? TIMEFRAME_TO_PERIOD['1h'];
}
