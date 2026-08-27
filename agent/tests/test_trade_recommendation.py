"""Tests for trade recommendation tool and SSE relay."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.tools.propose_trade_recommendation_tool import ProposeTradeRecommendationTool


def test_propose_trade_recommendation_quick_mode_rejected() -> None:
    tool = ProposeTradeRecommendationTool()
    result = json.loads(
        tool.execute(
            canonical_id="EUR_USD",
            direction="BUY",
            analysis_mode="quick",
            entry_zone_low=1.08,
            entry_zone_high=1.082,
            stop_loss=1.075,
        )
    )
    assert result["status"] == "error"


def test_propose_trade_recommendation_deep_persists(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path), raising=False)
    tool = ProposeTradeRecommendationTool()
    result = json.loads(
        tool.execute(
            canonical_id="EUR_USD",
            direction="BUY",
            analysis_mode="deep",
            entry_zone_low=1.08,
            entry_zone_high=1.082,
            preferred_entry=1.081,
            stop_loss=1.075,
            take_profits=[{"price": 1.09, "size_pct": 100}],
            session_open=True,
            chart_vision_ok=True,
        )
    )
    assert result["recommendation_id"].startswith("tr_")
    assert result["type"] == "trade.recommendation"
    assert isinstance(result.get("gate_results"), list)


def test_trade_recommendation_sse_relay(tmp_path: Path, monkeypatch) -> None:
    from src.api.sessions_routes import _trade_recommendation_frame_from_tool_result
    from src.trade_recommendation.store import save_recommendation

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path), raising=False)
    record = save_recommendation(
        {
            "canonical_id": "EUR_USD",
            "direction": "BUY",
            "timeframe": "H1",
            "plan_type": "trade",
            "execution_status": "ready",
            "publishable": True,
            "entry_zone": [1.08, 1.082],
            "stop_loss": 1.075,
            "gate_results": [],
        }
    )
    recommendation_id = record["recommendation_id"]
    event = SimpleNamespace(
        event_type="tool_result",
        session_id="s1",
        data={
            "tool": "propose_trade_recommendation",
            "status": "ok",
            "preview": json.dumps({"recommendation_id": recommendation_id})[:200],
        },
    )
    frame = _trade_recommendation_frame_from_tool_result(event)
    assert frame is not None
    assert "trade.recommendation" in frame
    assert recommendation_id in frame
