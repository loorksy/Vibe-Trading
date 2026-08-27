from app.services.backtest import BacktestEngine, BacktestConfig


def test_backtest_insufficient_data():
    engine = BacktestEngine()
    candles = [{"close": 1.0 + i * 0.001, "open": 1.0, "high": 1.01, "low": 0.99} for i in range(20)]
    signals = [{"direction": "BUY"} for _ in range(5)]
    result = engine.run(candles, signals, BacktestConfig(min_sample_size=30))
    assert result.confidence_label == "Insufficient data"
    assert result.sample_size == 5


def test_backtest_includes_cost_model():
    engine = BacktestEngine()
    candles = [{"close": 1.0 + i * 0.001, "open": 1.0, "high": 1.01, "low": 0.99} for i in range(100)]
    signals = [{"direction": "BUY"} for _ in range(40)]
    result = engine.run(candles, signals)
    assert result.equity_curve
    assert result.max_drawdown >= 0
    assert len(result.trades) == 40
