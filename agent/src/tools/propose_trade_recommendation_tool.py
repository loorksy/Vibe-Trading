"""``propose_trade_recommendation`` — gated, read-only trade recommendation proposal."""

from __future__ import annotations

import json
import uuid
from typing import Any

from src.agent.tools import BaseTool
from src.trade_recommendation.gate_runner import run_gates
from src.trade_recommendation.store import save_recommendation


class ProposeTradeRecommendationTool(BaseTool):
    """Persist a gated trade recommendation for surface execution only."""

    name = "propose_trade_recommendation"
    description = (
        "Propose a gated trade recommendation after deep analysis. READ-ONLY: "
        "persists the recommendation and returns a trade.recommendation payload; "
        "it does NOT place orders. Quick Scan mode must NOT call this tool — "
        "use analytical commentary only. Deep Analysis should call this after "
        "OANDA data, chart review, and gate checks."
    )
    parameters = {
        "type": "object",
        "properties": {
            "canonical_id": {"type": "string", "description": "OANDA canonical id, e.g. EUR_USD."},
            "direction": {"type": "string", "enum": ["BUY", "SELL"]},
            "timeframe": {"type": "string", "default": "H1"},
            "analysis_mode": {"type": "string", "enum": ["quick", "deep"], "default": "deep"},
            "analytical_bias": {"type": "string"},
            "entry_zone_low": {"type": "number"},
            "entry_zone_high": {"type": "number"},
            "preferred_entry": {"type": "number"},
            "stop_loss": {"type": "number"},
            "take_profits": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "price": {"type": "number"},
                        "size_pct": {"type": "number"},
                    },
                },
            },
            "session_id": {"type": "string"},
            "news_blocked": {"type": "boolean"},
            "session_open": {"type": "boolean"},
            "chart_vision_ok": {"type": "boolean"},
            "expected_move_r": {"type": "number"},
        },
        "required": ["canonical_id", "direction", "stop_loss", "entry_zone_low", "entry_zone_high"],
    }
    repeatable = True
    is_readonly = True

    def execute(self, **kwargs: Any) -> str:
        analysis_mode = str(kwargs.get("analysis_mode") or "deep").strip().lower()
        if analysis_mode == "quick":
            return json.dumps(
                {
                    "status": "error",
                    "error": (
                        "Quick Scan is non-tradeable. Provide analysis in chat only; "
                        "call propose_trade_recommendation only for Deep Analysis."
                    ),
                },
                ensure_ascii=False,
            )

        canonical_id = str(kwargs.get("canonical_id") or "").strip()
        direction = str(kwargs.get("direction") or "").strip().upper()
        if not canonical_id or direction not in {"BUY", "SELL"}:
            return json.dumps(
                {"status": "error", "error": "canonical_id and direction (BUY|SELL) are required"},
                ensure_ascii=False,
            )

        draft: dict[str, Any] = {
            "recommendation_id": f"tr_{uuid.uuid4().hex}",
            "session_id": kwargs.get("session_id"),
            "canonical_id": canonical_id,
            "direction": direction,
            "timeframe": str(kwargs.get("timeframe") or "H1"),
            "analysis_mode": "deep",
            "analytical_bias": str(kwargs.get("analytical_bias") or ""),
            "plan_type": "trade",
            "execution_status": "ready",
            "entry_zone_low": float(kwargs["entry_zone_low"]),
            "entry_zone_high": float(kwargs["entry_zone_high"]),
            "preferred_entry": kwargs.get("preferred_entry"),
            "stop_loss": float(kwargs["stop_loss"]),
            "take_profits": list(kwargs.get("take_profits") or []),
            "news_blocked": bool(kwargs.get("news_blocked", False)),
            "session_open": bool(kwargs.get("session_open", True)),
            "chart_vision_ok": bool(kwargs.get("chart_vision_ok", True)),
            "expected_move_r": float(kwargs.get("expected_move_r") or 1.5),
        }

        try:
            gated, _, publishable = run_gates(draft)
        except (TypeError, ValueError) as exc:
            return json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False)

        if not publishable:
            gated["plan_type"] = gated.get("plan_type") or "watchlist"

        try:
            record = save_recommendation(gated)
        except ValueError as exc:
            return json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False)

        return json.dumps(record, ensure_ascii=False)
