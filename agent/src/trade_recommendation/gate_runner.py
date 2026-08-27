"""Run validation gates against a trade recommendation draft."""

from __future__ import annotations

from typing import Any

from src.gates.validation import GateContext, GateResult, ValidationGates
from src.providers.oanda.client import OandaClient, _oanda_to_display

DEFAULT_SPREAD_LIMIT_PIPS = 3.0
DEFAULT_DIVERGENCE_THRESHOLD_PCT = 0.5
PIP_SCALE = {
    "JPY": 0.01,
    "XAU": 0.1,
    "XAG": 0.01,
}


def _pip_size(canonical_id: str) -> float:
    upper = canonical_id.upper()
    if "JPY" in upper:
        return PIP_SCALE["JPY"]
    if upper.startswith("XAU"):
        return PIP_SCALE["XAU"]
    if upper.startswith("XAG"):
        return PIP_SCALE["XAG"]
    return 0.0001


def _spread_pips(canonical_id: str, bid: float, ask: float) -> float:
    pip = _pip_size(canonical_id)
    if pip <= 0:
        return 0.0
    return abs(ask - bid) / pip


def build_gate_context(draft: dict[str, Any], *, client: OandaClient | None = None) -> GateContext:
    oanda = client or OandaClient()
    canonical_id = str(draft["canonical_id"])
    price = oanda.get_price(canonical_id) or {}
    mid = float(price.get("mid") or draft.get("preferred_entry") or 0)
    bid = float(price.get("bid") or mid)
    ask = float(price.get("ask") or mid)
    spread_pips = _spread_pips(canonical_id, bid, ask) if mid else float(draft.get("spread_pips") or 0)

    entry_low = float(draft.get("entry_zone_low", draft.get("entry_zone", [mid, mid])[0]))
    entry_high = float(draft.get("entry_zone_high", draft.get("entry_zone", [mid, mid])[-1]))
    if entry_low > entry_high:
        entry_low, entry_high = entry_high, entry_low

    return GateContext(
        canonical_id=canonical_id,
        timeframe=str(draft.get("timeframe") or "H1"),
        direction=str(draft.get("direction") or "BUY").upper(),
        analytical_bias=str(draft.get("analytical_bias") or ""),
        plan_type=str(draft.get("plan_type") or "trade"),
        execution_status=str(draft.get("execution_status") or "ready"),
        entry_zone=(entry_low, entry_high),
        preferred_entry=float(draft.get("preferred_entry") or mid),
        stop_loss=float(draft.get("stop_loss") or 0),
        take_profits=list(draft.get("take_profits") or []),
        spread_pips=spread_pips,
        session_open=bool(draft.get("session_open", True)),
        news_blocked=bool(draft.get("news_blocked", False)),
        price_at_analysis=float(draft.get("price_at_analysis") or mid),
        current_price=mid,
        oanda_price=mid,
        twelve_data_price=draft.get("twelve_data_price"),
        divergence_threshold_pct=float(
            draft.get("divergence_threshold_pct", DEFAULT_DIVERGENCE_THRESHOLD_PCT)
        ),
        spread_limit_pips=float(draft.get("spread_limit_pips", DEFAULT_SPREAD_LIMIT_PIPS)),
        expected_move_r=float(draft.get("expected_move_r") or 1.5),
        chart_vision_ok=bool(draft.get("chart_vision_ok", True)),
    )


def apply_gate_actions(draft: dict[str, Any], results: list[GateResult]) -> dict[str, Any]:
    out = dict(draft)
    for result in results:
        if result.action == "change_plan_type":
            out["plan_type"] = "watchlist"
        if result.action == "change_execution_status":
            out["execution_status"] = "stale"
    return out


def run_gates(draft: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], bool]:
    gates = ValidationGates()
    ctx = build_gate_context(draft)
    results = gates.run_all(ctx)
    publishable = gates.should_publish(results)
    updated = apply_gate_actions(draft, results)
    if not publishable:
        updated["execution_status"] = "refused"
        updated["plan_type"] = updated.get("plan_type") or "watchlist"
    elif updated.get("execution_status") not in ("stale", "refused"):
        updated["execution_status"] = "ready"
    serialized = [
        {
            "gate": r.gate_name,
            "passed": r.passed,
            "reason": r.reason,
            "action": r.action,
        }
        for r in results
    ]
    updated["gate_results"] = serialized
    updated["publishable"] = publishable and updated.get("execution_status") == "ready"
    updated["display_symbol"] = _oanda_to_display(str(updated["canonical_id"]))
    updated["entry_zone"] = [
        float(updated.get("entry_zone_low", ctx.entry_zone[0])),
        float(updated.get("entry_zone_high", ctx.entry_zone[1])),
    ]
    return updated, serialized, bool(updated["publishable"])
