import pytest
from app.services.chart_vision import ChartVisionService


SAMPLE_CANDLES = [
    {"time": "2026-08-27T10:00:00Z", "open": 1.08, "high": 1.085, "low": 1.079, "close": 1.084},
    {"time": "2026-08-27T11:00:00Z", "open": 1.084, "high": 1.09, "low": 1.083, "close": 1.088},
    {"time": "2026-08-27T12:00:00Z", "open": 1.088, "high": 1.092, "low": 1.086, "close": 1.09},
]


def test_render_chart_produces_base64():
    service = ChartVisionService()
    result = service._render_chart(SAMPLE_CANDLES, "EUR_USD", "1h")
    assert result is not None
    assert len(result) > 100


def test_render_chart_empty_returns_none():
    service = ChartVisionService()
    result = service._render_chart([], "EUR_USD", "1h")
    assert result is None
