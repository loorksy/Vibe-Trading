import pytest
from app.gates.validation import GateContext, ValidationGates


def _base_ctx(**overrides):
    defaults = dict(
        canonical_id="EUR_USD",
        timeframe="1h",
        direction="BUY",
        analytical_bias="BUY",
        plan_type="immediate",
        execution_status="active_now",
        entry_zone=(1.0840, 1.0860),
        preferred_entry=1.0850,
        stop_loss=1.0820,
        take_profits=[{"level": 1, "price": 1.0880}],
        spread_pips=1.5,
        session_open=True,
        news_blocked=False,
        price_at_analysis=1.0850,
        current_price=1.0850,
        oanda_price=1.0850,
        twelve_data_price=1.0851,
        divergence_threshold_pct=0.15,
        spread_limit_pips=3.0,
        expected_move_r=2.0,
        chart_vision_ok=True,
    )
    defaults.update(overrides)
    return GateContext(**defaults)


def test_gates_never_flip_direction():
    gates = ValidationGates()
    ctx = _base_ctx(direction="BUY", analytical_bias="BUY")
    results = gates.run_all(ctx)
    for r in results:
        assert "SELL" not in r.reason or "flip" not in r.reason.lower()


def test_news_gate_blocks():
    gates = ValidationGates()
    ctx = _base_ctx(news_blocked=True)
    results = gates.run_all(ctx)
    news = next(r for r in results if r.gate_name == "news_event")
    assert not news.passed


def test_divergence_blocks():
    gates = ValidationGates()
    ctx = _base_ctx(oanda_price=1.0850, twelve_data_price=1.1000, divergence_threshold_pct=0.15)
    results = gates.run_all(ctx)
    price_gate = next(r for r in results if r.gate_name == "live_price_reverification")
    assert not price_gate.passed


def test_chart_vision_required():
    gates = ValidationGates()
    ctx = _base_ctx(chart_vision_ok=False)
    results = gates.run_all(ctx)
    price_gate = next(r for r in results if r.gate_name == "live_price_reverification")
    assert not price_gate.passed
    assert "Chart vision" in price_gate.reason
