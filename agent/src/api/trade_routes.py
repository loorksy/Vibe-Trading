"""Surface-only trade execution routes (never exposed as agent tools)."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.trade_recommendation import RecommendationError, load_recommendation, mark_executed
from src.trading.connectors.metaapi.symbols import canonical_to_execution_symbol
from src.trading.service import place_order


class ExecuteTradeRequest(BaseModel):
    recommendation_id: str = Field(..., min_length=8)
    profile_id: str = Field("metaapi-live-trade")
    volume: float = Field(..., gt=0, description="Order volume in lots")
    session_id: str | None = None
    consent_ack: bool = False
    execution_symbol: str | None = None


def register_trade_routes(app: FastAPI, require_auth) -> None:
    @app.post("/executions", dependencies=[Depends(require_auth)])
    def execute_trade(payload: ExecuteTradeRequest) -> dict[str, Any]:
        if payload.consent_ack is not True:
            raise HTTPException(status_code=400, detail="consent_ack must be true to execute")

        try:
            recommendation = load_recommendation(payload.recommendation_id)
        except RecommendationError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        if recommendation.get("status") == "executed":
            raise HTTPException(status_code=409, detail="recommendation already executed")
        if recommendation.get("execution_status") != "ready" or not recommendation.get("publishable"):
            raise HTTPException(status_code=400, detail="recommendation is not executable")

        take_profits = recommendation.get("take_profits") or []
        take_profit = None
        if take_profits:
            first = take_profits[0]
            if isinstance(first, dict) and first.get("price") is not None:
                take_profit = float(first["price"])

        exec_symbol = payload.execution_symbol or canonical_to_execution_symbol(
            str(recommendation["canonical_id"]),
            recommendation.get("execution_symbol"),
        )

        result = place_order(
            symbol=str(recommendation["canonical_id"]),
            profile_id=payload.profile_id,
            side=str(recommendation["direction"]),
            quantity=payload.volume,
            session_id=payload.session_id or str(recommendation.get("session_id") or ""),
            stop_loss=float(recommendation.get("stop_loss") or 0) or None,
            take_profit=take_profit,
            execution_symbol=exec_symbol,
            client_id=payload.recommendation_id,
        )
        if result.get("status") != "ok":
            raise HTTPException(status_code=502, detail=result.get("error") or "execution failed")

        public = mark_executed(payload.recommendation_id, result)
        return {"status": "ok", "recommendation": public, "execution": result}
