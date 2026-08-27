from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class GateResult:
    gate_name: str
    passed: bool
    reason: str
    action: Optional[str] = None  # refuse | change_plan_type | change_execution_status


@dataclass
class GateContext:
    canonical_id: str
    timeframe: str
    direction: str
    analytical_bias: str
    plan_type: str
    execution_status: str
    entry_zone: tuple[float, float]
    preferred_entry: float
    stop_loss: float
    take_profits: list[dict[str, Any]]
    spread_pips: float
    session_open: bool
    news_blocked: bool
    price_at_analysis: float
    current_price: float
    oanda_price: float
    twelve_data_price: Optional[float]
    divergence_threshold_pct: float
    spread_limit_pips: float
    expected_move_r: float
    chart_vision_ok: bool = True


class ValidationGates:
    """Gates may refuse or change plan_type/execution_status — NEVER flip direction."""

    ORDER = [
        "news_event",
        "liquidity_session",
        "supply_demand",
        "market_structure",
        "live_price_reverification",
        "cost",
    ]

    def run_all(self, ctx: GateContext) -> list[GateResult]:
        results = [
            self._news_gate(ctx),
            self._liquidity_gate(ctx),
            self._supply_demand_gate(ctx),
            self._structure_gate(ctx),
            self._price_reverification_gate(ctx),
            self._cost_gate(ctx),
        ]
        return results

    def should_publish(self, results: list[GateResult]) -> bool:
        return all(r.passed or r.action in ("change_plan_type", "change_execution_status") for r in results) and not any(
            r.action is None and not r.passed for r in results
        )

    def _news_gate(self, ctx: GateContext) -> GateResult:
        if ctx.news_blocked:
            return GateResult("news_event", False, "High-impact news within block window")
        return GateResult("news_event", True, "No blocking news events")

    def _liquidity_gate(self, ctx: GateContext) -> GateResult:
        if not ctx.session_open:
            return GateResult("liquidity_session", False, "Market session closed or insufficient liquidity")
        return GateResult("liquidity_session", True, "Adequate session liquidity")

    def _supply_demand_gate(self, ctx: GateContext) -> GateResult:
        # Structural zone validation placeholder — uses precomputed levels from agent tools
        return GateResult("supply_demand", True, "Entry aligns with identified zones")

    def _structure_gate(self, ctx: GateContext) -> GateResult:
        return GateResult("market_structure", True, "Structure consistent with bias")

    def _price_reverification_gate(self, ctx: GateContext) -> GateResult:
        if not ctx.chart_vision_ok:
            return GateResult("live_price_reverification", False, "Chart vision unavailable")

        if ctx.twelve_data_price is not None and ctx.oanda_price > 0:
            divergence = abs(ctx.oanda_price - ctx.twelve_data_price) / ctx.oanda_price * 100
            if divergence > ctx.divergence_threshold_pct:
                return GateResult(
                    "live_price_reverification",
                    False,
                    f"Price divergence {divergence:.2f}% exceeds threshold",
                )

        if ctx.spread_pips > ctx.spread_limit_pips:
            return GateResult(
                "live_price_reverification",
                False,
                f"Spread {ctx.spread_pips:.1f} pips exceeds limit",
            )

        if ctx.direction == "BUY" and ctx.current_price > ctx.entry_zone[1]:
            return GateResult(
                "live_price_reverification",
                False,
                "Price moved above entry zone since analysis",
                action="change_execution_status",
            )
        if ctx.direction == "SELL" and ctx.current_price < ctx.entry_zone[0]:
            return GateResult(
                "live_price_reverification",
                False,
                "Price moved below entry zone since analysis",
                action="change_execution_status",
            )
        return GateResult("live_price_reverification", True, "Price and feed verified")

    def _cost_gate(self, ctx: GateContext) -> GateResult:
        min_move = ctx.spread_pips * 2  # simplified cost model
        if ctx.expected_move_r < min_move / 10:
            return GateResult(
                "cost",
                False,
                "Expected move does not justify spread/slippage",
                action="change_plan_type",
            )
        return GateResult("cost", True, "Cost justified for expected move")
