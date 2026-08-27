"""``run_validation_gates`` — expose the six trading validation gates to the agent."""

from __future__ import annotations

import json
from typing import Any

from src.agent.tools import BaseTool
from src.gates.validation import ValidationGates
from src.trade_recommendation.gate_runner import build_gate_context


class RunValidationGatesTool(BaseTool):
    """Run all six validation gates for a proposed trade setup."""

    name = "run_validation_gates"
    description = (
        "Run the six validation gates (news, liquidity, zones, structure, price "
        "reverification, cost) for a trade setup. Gates may refuse or change "
        "plan_type/execution_status but NEVER flip BUY↔SELL."
    )
    parameters = {
        "type": "object",
        "properties": {
            "canonical_id": {"type": "string"},
            "timeframe": {"type": "string"},
            "direction": {"type": "string", "enum": ["BUY", "SELL"]},
            "analytical_bias": {"type": "string"},
            "plan_type": {"type": "string"},
            "execution_status": {"type": "string"},
            "entry_zone_low": {"type": "number"},
            "entry_zone_high": {"type": "number"},
            "preferred_entry": {"type": "number"},
            "stop_loss": {"type": "number"},
            "take_profits": {"type": "array", "items": {"type": "object"}},
            "news_blocked": {"type": "boolean"},
            "session_open": {"type": "boolean"},
            "chart_vision_ok": {"type": "boolean"},
            "expected_move_r": {"type": "number"},
        },
        "required": ["canonical_id", "direction", "stop_loss"],
    }
    repeatable = True
    is_readonly = True
    deterministic = True

    def execute(self, **kwargs: Any) -> str:
        try:
            ctx = build_gate_context(kwargs)
        except (TypeError, ValueError, KeyError) as exc:
            return json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False)
        gates = ValidationGates()
        results = gates.run_all(ctx)
        return json.dumps(
            {
                "status": "ok",
                "results": [
                    {
                        "gate": r.gate_name,
                        "passed": r.passed,
                        "reason": r.reason,
                        "action": r.action,
                    }
                    for r in results
                ],
                "should_publish": gates.should_publish(results),
            },
            ensure_ascii=False,
        )
