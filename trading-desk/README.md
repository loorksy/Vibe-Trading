# Trading Desk — AI Trading Assistant Platform

Personal trading desk for a single operator: ask in Arabic, English, or Turkish and get structured trade plans on any OANDA instrument, with chart vision, validation gates, versioned bots (code + mind), and MetaApi execution.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.12+

### 1. Environment

```bash
cd trading-desk
cp .env.example .env
# Edit .env with OANDA, Anthropic, MetaApi, Finnhub keys
```

### 2. Start infrastructure

```bash
docker compose up -d postgres redis
```

### 3. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

In another terminal, start the Arq worker:

```bash
cd backend
arq app.workers.main.WorkerSettings
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — login with `operator` / `operator` (default dev password).

### 5. Android APK (Capacitor)

```bash
cd frontend && npm run build
cd ../capacitor && npm install && npx cap add android && npx cap sync
npx cap open android
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  React UI   │────▶│  FastAPI     │────▶│  PostgreSQL     │
│  (Vite)     │ SSE │  + Arq       │     │  + pgvector     │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         OANDA API    Claude Agent   MetaApi
         (analysis)  SDK (agents)   (execution only)
              │
         Twelve Data (cross-check only)
```

See [documentation/ARCHITECTURE.md](documentation/ARCHITECTURE.md) for full details.

## Daily UI Surfaces

| Route | Mode |
|-------|------|
| `/` | Ask (chat) — Quick Scan / Deep Analysis |
| `/today` | Scan Today — news, calendar, movers |
| `/build` | Build — strategy/bot creation |

All other pages are secondary navigation.

## Key Principles

- **OANDA only** for analysis candles/prices; MetaApi for execution only
- **No MCP** — agent tools are native Python functions on Claude Agent SDK
- **No free-text symbols** — searchable picker from OANDA catalog
- **Gates never flip direction** — BUY/SELL only, never WAIT
- **Execution** only via explicit user command naming a saved recommendation or bot
- **Bots** = CODE (versioned Python strategy) + MIND (rationale writer before every order)

## API Routes

| Route | Auth | Description |
|-------|------|-------------|
| `POST /api/auth/login` | No | JWT login |
| `POST /api/chat/message` | Yes | Chat with agent |
| `POST /api/recommendations/analyze` | Yes | Deep analysis |
| `GET /api/instruments` | Yes | OANDA catalog |
| `POST /api/executions` | Yes | Execute saved recommendation |
| `POST /api/bots/stop-all` | Yes | Emergency kill switch |
| `GET /health` | No | Health check |

## Tests

```bash
cd backend && pytest
cd frontend && npm test
```

## Disclaimer

This is personal analysis software, not fund or asset management. Markets carry risk of loss. No performance promises are shown in the UI.
