# Backtest Engine Methodology

## Principles

1. **Mandatory cost model** — every backtest includes spread + slippage; never skippable
2. **OANDA historical data** — sole price source for backtests
3. **Minimum sample floor** — below threshold, show "Insufficient data" never a fabricated win rate
4. **Full output** — equity curve + trade list + max drawdown, never a single number

## Cost Model

```python
cost_per_trade = (spread_pips + slippage_pips) * pip_value * position_size
```

Default: 1.5 pip spread + 0.5 pip slippage.

## Nightly Incremental

Arq cron job at 02:00 extends backtests as new candles arrive — incremental, not full re-run.

## Parameter Optimizer

Results tagged "Fragile" when out-of-sample performance collapses. Never presented as ready for live without warning.

## Confidence Label

- `n < min_sample_size` → "Insufficient data"
- `n >= min_sample_size` → real win rate with sample count
