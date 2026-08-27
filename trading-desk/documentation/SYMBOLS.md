# OANDA Catalog + Broker Alias Mapping

## OANDA Instrument Catalog

On startup and periodic refresh (Arq cron every 12h):

```
GET /v3/accounts/{accountId}/instruments
```

Each instrument stored as:
- `canonical_id` — OANDA name (e.g. `EUR_USD`, `XAU_USD`)
- `display_symbol` — UI display (e.g. `EURUSD`)
- `asset_class` — as reported by OANDA
- `tradable` — boolean

The symbol picker searches this catalog. **No free-text ticker input anywhere.**

## Broker Symbol Aliases

Broker/MT5 symbols differ from OANDA:

| OANDA canonical | Broker examples |
|---------------|-----------------|
| EUR_USD | EURUSD, EURUSDm, EURUSD.pro, EURUSD.m, EURUSD# |
| XAU_USD | XAUUSD, XAUUSDm, GOLD |

Mapping stored in `broker_symbol_aliases`:
- `account_id` + `canonical_id` → `execution_symbol`
- Test-resolved via MetaApi before save

## Rules

- Analysis, charts, gates, backtests → always `canonical_id`
- Orders to MetaApi → always `execution_symbol`
- Unmapped instruments → analyzable, never executable
- Never send `EUR_USD` to a broker expecting `EURUSDm`

## Account Page

Operator maps each intended live instrument per account. Test button calls MetaApi symbol list to verify.
