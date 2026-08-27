import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.agents.orchestrator import AnalysisRequest, TradingAgentOrchestrator
from app.agents.tools import build_tool_registry
from app.core.auth import get_current_user
from app.database import get_db
from app.gates.validation import GateContext, ValidationGates
from app.models import AgentRunLog, ChatMessage, ChatSession, Recommendation
from app.schemas import ChatMessageRequest, RecommendationCreate, RecommendationOut
from app.services.market_data import FeedHealthService, OandaService

router = APIRouter(tags=["chat", "recommendations"])


@router.post("/chat/message")
async def send_message(
    body: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    session_id = body.session_id
    if not session_id:
        session = ChatSession()
        db.add(session)
        await db.flush()
        session_id = session.id
    else:
        session = await db.get(ChatSession, session_id)
        if not session:
            raise HTTPException(404, "Session not found")

    user_msg = ChatMessage(session_id=session_id, role="user", content=body.message, analysis_mode=body.mode)
    db.add(user_msg)

    tools = build_tool_registry(db)
    orchestrator = TradingAgentOrchestrator(tools)

    chart_snapshots = None
    if body.mode == "deep_analysis" and body.canonical_id:
        chart_snapshots = await _capture_chart_vision(body.canonical_id, body.timeframe)

    request = AnalysisRequest(
        canonical_id=body.canonical_id or "EUR_USD",
        timeframe=body.timeframe,
        mode=body.mode,
        user_message=body.message,
        chart_snapshots=chart_snapshots,
    )
    result = await orchestrator.run_analysis(request)

    artifacts = []
    if result.get("recommendation"):
        rec_data = result["recommendation"]
        rec = Recommendation(**rec_data)
        db.add(rec)
        await db.flush()
        artifacts.append({"type": "recommendation_card", "data": {"id": rec.id, **rec_data}})
        db.add(
            AgentRunLog(
                session_id=session_id,
                recommendation_id=rec.id,
                analysis_mode=body.mode,
                transcript=result["transcript"],
            )
        )

    assistant_content = (
        "Quick scan complete — not a tradeable recommendation."
        if body.mode == "quick_scan"
        else ("Analysis complete." if result.get("published") else result.get("error", "Analysis refused by gates."))
    )

    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=assistant_content,
        artifacts=artifacts or None,
        analysis_mode=body.mode,
    )
    db.add(assistant_msg)

    return {
        "session_id": session_id,
        "message": assistant_content,
        "artifacts": artifacts,
        "transcript_available": bool(result.get("transcript")),
    }


@router.get("/chat/sessions")
async def list_sessions(db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    result = await db.execute(select(ChatSession).order_by(ChatSession.updated_at.desc()).limit(50))
    return [{"id": s.id, "title": s.title, "created_at": s.created_at.isoformat()} for s in result.scalars()]


@router.get("/chat/sessions/{session_id}/messages")
async def get_messages(session_id: str, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    )
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "artifacts": m.artifacts,
            "analysis_mode": m.analysis_mode,
            "created_at": m.created_at.isoformat(),
        }
        for m in result.scalars()
    ]


@router.get("/chat/sessions/{session_id}/agent-log")
async def get_agent_log(session_id: str, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    result = await db.execute(
        select(AgentRunLog).where(AgentRunLog.session_id == session_id).order_by(AgentRunLog.created_at.desc())
    )
    log = result.scalars().first()
    if not log:
        return {"transcript": []}
    return {"transcript": log.transcript, "gate_results": log.gate_results}


@router.post("/recommendations/analyze")
async def new_analysis(
    body: RecommendationCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    if body.mode != "deep_analysis":
        raise HTTPException(400, "New Analysis requires deep_analysis mode")

    chart_snapshots = await _capture_chart_vision(body.canonical_id, body.timeframe)
    if not chart_snapshots:
        raise HTTPException(503, "Chart vision unavailable")

    tools = build_tool_registry(db)
    orchestrator = TradingAgentOrchestrator(tools)
    request = AnalysisRequest(
        canonical_id=body.canonical_id,
        timeframe=body.timeframe,
        mode="deep_analysis",
        user_message="New Analysis",
        chart_snapshots=chart_snapshots,
    )
    result = await orchestrator.run_analysis(request)
    if not result.get("recommendation"):
        return {"published": False, "error": result.get("error", "Gates refused publication")}

    rec_data = result["recommendation"]
    gates = ValidationGates()
    oanda = OandaService()
    price = await oanda.get_price(body.canonical_id)
    feed = await FeedHealthService().check_divergence(body.canonical_id)

    ctx = GateContext(
        canonical_id=body.canonical_id,
        timeframe=body.timeframe,
        direction=rec_data["direction"],
        analytical_bias=rec_data["analytical_bias"],
        plan_type=rec_data["plan_type"],
        execution_status=rec_data["execution_status"],
        entry_zone=(rec_data["entry_zone_low"], rec_data["entry_zone_high"]),
        preferred_entry=rec_data["preferred_entry"],
        stop_loss=rec_data["stop_loss"],
        take_profits=rec_data["take_profits"],
        spread_pips=(price or {}).get("spread", 0) * 10000,
        session_open=True,
        news_blocked=False,
        price_at_analysis=rec_data["preferred_entry"],
        current_price=(price or {}).get("mid", rec_data["preferred_entry"]),
        oanda_price=feed.get("oanda") or rec_data["preferred_entry"],
        twelve_data_price=feed.get("twelve_data"),
        divergence_threshold_pct=0.15,
        spread_limit_pips=3.0,
        expected_move_r=2.0,
        chart_vision_ok=True,
    )
    gate_results = gates.run_all(ctx)
    rec_data["gate_results"] = [
        {"gate": g.gate_name, "passed": g.passed, "reason": g.reason, "action": g.action} for g in gate_results
    ]

    if not gates.should_publish(gate_results):
        return {"published": False, "gate_results": rec_data["gate_results"]}

    rec = Recommendation(**rec_data)
    db.add(rec)
    await db.flush()
    db.add(
        AgentRunLog(
            recommendation_id=rec.id,
            analysis_mode="deep_analysis",
            transcript=result["transcript"],
            gate_results=rec_data["gate_results"],
        )
    )
    return {"published": True, "recommendation": RecommendationOut.model_validate(rec)}


@router.get("/recommendations", response_model=list[RecommendationOut])
async def list_recommendations(db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    result = await db.execute(select(Recommendation).order_by(Recommendation.created_at.desc()).limit(100))
    return result.scalars().all()


@router.get("/recommendations/{rec_id}", response_model=RecommendationOut)
async def get_recommendation(rec_id: str, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    rec = await db.get(Recommendation, rec_id)
    if not rec:
        raise HTTPException(404, "Not found")
    return rec


async def _capture_chart_vision(canonical_id: str, timeframe: str) -> Optional[dict]:
    oanda = OandaService()
    timeframes = ["15m", "1h", "4h"]
    if timeframe not in timeframes:
        timeframes.append(timeframe)
    snapshots = {}
    for tf in timeframes:
        gran = {"15m": "M15", "1h": "H1", "4h": "H4"}.get(tf, "H1")
        candles = await oanda.get_candles(canonical_id, gran, 100)
        if candles:
            snapshots[tf] = {"ohlc": candles[-20:], "image_ref": f"snapshot:{canonical_id}:{tf}"}
    return snapshots if snapshots else None
