"""Tests for trading validation gates."""

from src.gates.validation import GateContext, ValidationGates


def _ctx(**overrides) -> GateContext:
    base = dict(
        canonical_id="EUR_USD",
        timeframe="H1",
        direction="BUY",
        analytical_bias="bullish",
        plan_type="trade",
        execution_status="ready",
        entry_zone=(1.0800, 1.0820),
        preferred_entry=1.0810,
        stop_loss=1.0750,
        take_profits=[{"price": 1.0900, "size_pct": 100}],
        spread_pips=1.2,
        session_open=True,
        news_blocked=False,
        price_at_analysis=1.0810,
        current_price=1.0815,
        oanda_price=1.0815,
        twelve_data_price=1.0814,
        divergence_threshold_pct=0.5,
        spread_limit_pips=3.0,
        expected_move_r=2.0,
        chart_vision_ok=True,
    )
    base.update(overrides)
    return GateContext(**base)


def test_all_gates_pass() -> None:
    gates = ValidationGates()
    results = gates.run_all(_ctx())
    assert gates.should_publish(results)
    assert all(r.passed or r.action for r in results)


def test_news_gate_blocks() -> None:
    gates = ValidationGates()
    results = gates.run_all(_ctx(news_blocked=True))
    news = next(r for r in results if r.gate_name == "news_event")
    assert not news.passed
    assert not gates.should_publish(results)


def test_price_gate_never_flips_direction() -> None:
    gates = ValidationGates()
    results = gates.run_all(_ctx(direction="BUY", current_price=1.0900))
    rev = next(r for r in results if r.gate_name == "live_price_reverification")
    assert not rev.passed
    assert rev.action == "change_execution_status"
    assert rev.action != "SELL"
