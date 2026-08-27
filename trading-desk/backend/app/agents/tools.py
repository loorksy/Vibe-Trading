"""Native agent tools — READ/ANALYSIS only. Execution is NEVER an agent tool."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import AgentToolRegistry
from app.gates.validation import GateContext, ValidationGates
from app.models import AgentMemory, Bot, Execution, Recommendation
from app.services.finnhub import FinnhubService
from app.services.market_data import FeedHealthService, OandaService


def build_tool_registry(db: AsyncSession) -> AgentToolRegistry:
    registry = AgentToolRegistry()
    oanda = OandaService()
    finnhub = FinnhubService()
    feeds = FeedHealthService()
    gates = ValidationGates()

    async def get_market_data(canonical_id: str, timeframe: str = "H1", count: int = 200) -> dict[str, Any]:
        granularity = _map_timeframe(timeframe)
        candles = await oanda.get_candles(canonical_id, granularity, count)
        price = await oanda.get_price(canonical_id)
        return {"candles": candles, "price": price, "source": "oanda"}

    async def get_news_sentiment(canonical_id: str) -> dict[str, Any]:
        news = await finnhub.get_news()
        calendar = await finnhub.get_economic_calendar()
        return {"news": news[:10], "calendar": calendar[:10]}

    async def check_feed_health(canonical_id: str = "EUR_USD") -> dict[str, Any]:
        return await feeds.check_divergence(canonical_id)

    async def run_validation_gates(payload: dict[str, Any]) -> dict[str, Any]:
        ctx = GateContext(**payload)
        results = gates.run_all(ctx)
        return {
            "results": [
                {"gate": r.gate_name, "passed": r.passed, "reason": r.reason, "action": r.action}
                for r in results
            ],
            "should_publish": gates.should_publish(results),
        }

    async def recall_similar_cases(canonical_id: str, limit: int = 5) -> dict[str, Any]:
        result = await db.execute(
            select(AgentMemory)
            .where(AgentMemory.canonical_id == canonical_id)
            .order_by(AgentMemory.created_at.desc())
            .limit(limit)
        )
        memories = result.scalars().all()
        if len(memories) < 3:
            return {"count": len(memories), "summary": "Insufficient data", "cases": []}
        outcomes = [m.outcome for m in memories]
        tp_count = sum(1 for o in outcomes if o and o.startswith("tp"))
        return {
            "count": len(memories),
            "summary": f"{len(memories)} similar setups — {tp_count} hit TP, {len(outcomes) - tp_count} hit SL/expired",
            "cases": [{"outcome": m.outcome, "context": m.context_text[:200]} for m in memories],
        }

    async def get_portfolio_exposure() -> dict[str, Any]:
        result = await db.execute(select(Execution).where(Execution.status == "open"))
        positions = result.scalars().all()
        total_r = sum(getattr(p, "risk_r", 1.0) for p in positions)
        by_symbol: dict[str, float] = {}
        for p in positions:
            by_symbol[p.canonical_id] = by_symbol.get(p.canonical_id, 0) + 1.0
        warnings = []
        if len(by_symbol) >= 2:
            warnings.append("Multiple positions may represent correlated USD exposure")
        return {"total_risk_r": total_r, "positions": len(positions), "by_symbol": by_symbol, "warnings": warnings}

    async def get_bot_status() -> dict[str, Any]:
        result = await db.execute(select(Bot))
        bots = result.scalars().all()
        return {
            "running_count": sum(1 for b in bots if b.is_running),
            "bots": [
                {
                    "id": b.id,
                    "name": b.name,
                    "symbol": b.canonical_id,
                    "state": b.state,
                    "is_running": b.is_running,
                }
                for b in bots
            ],
        }

    async def get_recommendation(recommendation_id: str) -> dict[str, Any]:
        rec = await db.get(Recommendation, recommendation_id)
        if not rec:
            return {"error": "Not found"}
        return {"id": rec.id, "direction": rec.direction, "execution_status": rec.execution_status}

    registry.register("get_market_data", get_market_data, "OANDA candles and live price")
    registry.register("get_news_sentiment", get_news_sentiment, "Finnhub news and calendar")
    registry.register("check_feed_health", check_feed_health, "OANDA vs Twelve Data divergence")
    registry.register("run_validation_gates", run_validation_gates, "Run all validation gates")
    registry.register("recall_similar_cases", recall_similar_cases, "pgvector similar past cases")
    registry.register("get_portfolio_exposure", get_portfolio_exposure, "Aggregate open position risk in R")
    registry.register("get_bot_status", get_bot_status, "Read-only bot list and status")
    registry.register("get_recommendation", get_recommendation, "Fetch saved recommendation by ID")
    return registry


def _map_timeframe(tf: str) -> str:
    mapping = {
        "1m": "M1", "5m": "M5", "15m": "M15", "30m": "M30",
        "1h": "H1", "4h": "H4", "1d": "D", "1w": "W",
    }
    return mapping.get(tf.lower(), "H1")
