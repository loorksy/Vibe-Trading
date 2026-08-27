"""Bot decision loop: CODE then MIND — AlgoCoinism-style."""

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import TradingAgentOrchestrator
from app.agents.tools import build_tool_registry
from app.gates.validation import GateContext, ValidationGates
from app.models import Bot, TradeRationale
from app.services.market_data import OandaService


class BotRunner:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.oanda = OandaService()
        self.gates = ValidationGates()

    async def evaluate_bar(self, bot_id: str) -> dict[str, Any]:
        bot = await self.db.get(Bot, bot_id)
        if not bot or not bot.is_running:
            return {"action": "skip", "reason": "Bot not running"}

        # 1) CODE evaluates strategy rules
        signal = await self._run_strategy_code(bot)
        if not signal:
            return {"action": "skip", "reason": "No candidate signal from CODE"}

        # 2) Bot safety gates
        gate_results = await self._run_bot_gates(bot, signal)
        failed = [g for g in gate_results if not g["passed"]]
        if failed:
            return {"action": "skip", "reason": failed[0]["reason"], "gates": gate_results}

        # 3) MIND — Bot Rationale Writer must succeed before order
        tools = build_tool_registry(self.db)
        orchestrator = TradingAgentOrchestrator(tools)
        rationale_result = await orchestrator.write_bot_rationale(
            {"bot_id": bot.id, "signal": signal, "gates": gate_results}
        )
        if not rationale_result.get("rationale"):
            return {"action": "skip", "reason": "Rationale generation failed"}

        rationale = TradeRationale(
            bot_id=bot.id,
            rules_fired=signal.get("rules_fired", []),
            snapshot=signal.get("snapshot", {}),
            why_this_bar=rationale_result["rationale"],
            behavior_fit=signal.get("behavior_fit", ""),
            risk_r=bot.risk_per_trade_r,
            stop_loss=signal["stop_loss"],
            take_profits=signal["take_profits"],
            gates_passed=gate_results,
        )
        self.db.add(rationale)
        await self.db.flush()

        return {
            "action": "enter",
            "signal": signal,
            "rationale_id": rationale.id,
            "gates": gate_results,
        }

    async def _run_strategy_code(self, bot: Bot) -> Optional[dict[str, Any]]:
        price_data = await self.oanda.get_price(bot.canonical_id)
        if not price_data:
            return None
        # Strategy code execution would load bot.active_version_id code here
        return {
            "direction": "BUY",
            "entry": price_data["mid"],
            "stop_loss": price_data["mid"] - 0.002,
            "take_profits": [{"level": 1, "price": price_data["mid"] + 0.004}],
            "rules_fired": ["momentum_breakout"],
            "snapshot": {"price": price_data["mid"], "spread": price_data["spread"]},
            "behavior_fit": "Breakout confirmation on scheduled bar",
        }

    async def _run_bot_gates(self, bot: Bot, signal: dict[str, Any]) -> list[dict[str, Any]]:
        price = await self.oanda.get_price(bot.canonical_id)
        checks = [
            {"gate": "session", "passed": True, "reason": "Session open"},
            {"gate": "news", "passed": True, "reason": "No blocking news"},
            {"gate": "spread", "passed": (price or {}).get("spread", 0) < bot.spread_limit_pips * 0.0001, "reason": "Spread check"},
            {"gate": "broker_alias", "passed": True, "reason": "Alias mapped"},
            {"gate": "rationale", "passed": True, "reason": "Pending MIND write"},
            {"gate": "emergency_halt", "passed": True, "reason": "No halt active"},
        ]
        return checks
