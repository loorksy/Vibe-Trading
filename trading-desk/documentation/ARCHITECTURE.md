# Architecture

## System Overview

Trading Desk is a single-operator AI trading assistant with three daily surfaces (Ask, Scan Today, Build) and secondary pages for charting, bots, strategies, and account management.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, TypeScript, Vite, Zustand, Tailwind CSS |
| Charting | KLineChart Pro |
| Chat artifacts | CopilotKit (integration point) |
| Mobile | Capacitor (Android APK) |
| Backend | Python 3.12, FastAPI (async) |
| ORM | SQLAlchemy 2.0 async + Alembic |
| Queue | Arq (Redis) |
| Database | PostgreSQL + pgvector |
| Cache/PubSub | Redis |
| Agent runtime | Claude Agent SDK (sole orchestrator) |

## Agent Architecture

Adapted role/debate patterns from [TradingAgents](https://github.com/TauricResearch/TradingAgents) and [crewAI](https://github.com/crewAIInc/crewAI) — **architectural reference only**. The only running orchestrator is Claude Agent SDK calling native Python tools.

### Roles

1. Technical Analyst — chart vision + OHLC
2. Risk Manager — ATR-buffered stops
3. News/Sentiment Analyst — Finnhub ranked news
4. Bull Researcher — case FOR
5. Bear Researcher — case AGAINST
6. Debate Moderator — limited rounds, resolves direction
7. Trader — formats structured recommendation
8. Bot Rationale Writer — "why this trade now" for bot fills

### Model Tiers

- **Quick Scan**: fast path, numbers only, NOT tradeable
- **Deep Analysis**: chart vision mandatory + full pipeline + all gates

### Agent Tools (READ/ANALYSIS only)

- `get_market_data` — OANDA candles/price
- `get_news_sentiment` — Finnhub
- `check_feed_health` — OANDA vs Twelve Data divergence
- `run_validation_gates`
- `recall_similar_cases` — pgvector memory
- `get_portfolio_exposure`
- `get_bot_status`
- `get_recommendation`

**Execution is NEVER an agent tool.**

## Data Flow

```
User → Chat UI → FastAPI → Agent Orchestrator
                              ├── OANDA (candles, prices)
                              ├── Finnhub (news)
                              ├── Gates (6 ordered checks)
                              └── pgvector (similar cases)
                                    ↓
                              Recommendation (if gates pass)
                                    ↓
                    User explicitly executes → MetaApi (mapped symbol)
```

## Validation Gates (ordered, never flip direction)

1. News/high-impact event
2. Liquidity/session
3. Supply/demand zone
4. Market structure
5. Live-price re-verification + divergence check
6. Cost (spread/slippage vs expected move)

## Bot Layer (CODE + MIND)

```
Scheduled bar/tick
  → CODE evaluates strategy rules
  → Bot safety gates (10 checks)
  → MIND writes rationale (required)
  → MetaApi order with SL attached
  → Rationale stored with execution row
```

## Symbol Mapping

```
OANDA canonical_id (EUR_USD) → analysis, charts, gates, backtests
Broker execution_symbol (EURUSDm) → MetaApi orders only
```

## Database Schema

See [documentation/DATABASE.md](documentation/DATABASE.md) for table reference.

## Feed Reliability

- OANDA = primary source of truth
- Twelve Data = cross-validation only
- Divergence beyond threshold → block new recommendations + banner

## Security

- JWT auth (single operator)
- Credentials encrypted at rest (Fernet)
- Rate limiting on chat/analysis
- Live promotion requires typed symbol or PIN confirmation
