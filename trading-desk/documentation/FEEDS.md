# OANDA / Twelve Data Feed Reconciliation

## Primary: OANDA

All analysis, charts, indicators, and gate computations use OANDA exclusively.

## Secondary: Twelve Data

Used only for cross-validation. Never used to compute indicators or levels directly.

## Divergence Check

Runs on:
- Every live-price re-verification gate
- Arq background job every 5 minutes

```python
divergence_pct = abs(oanda_price - twelve_data_price) / oanda_price * 100
healthy = divergence_pct <= threshold  # default 0.15%
```

## On Failure

| Condition | Action |
|-----------|--------|
| OANDA outage | Block new recommendations; conservative bot gates |
| Divergence exceeded | Block publishing; show "Price data unreliable" banner |
| Twelve Data unavailable | Continue on OANDA alone (log warning) |

## UI Banner

`FeedHealthBanner` component shows across app when `feed_health.healthy === false`.

Settings allow configuring `price_divergence_threshold_pct`.
