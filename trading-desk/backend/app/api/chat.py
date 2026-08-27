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
from app.services.chart_vision import ChartVisionService
from app.services.market_data import FeedHealthService, OandaService

router = APIRouter(tags=["chat", "recommendations"])


async def _run_chat_analysis(
    body: ChatMessageRequest,
    db: AsyncSession,
    session_id: str,
) -> dict:
    tools = build_tool_registry(db)
    orchestrator = TradingAgentOrchestrator(tools)
    oanda = OandaService()

    price = None
    if body.canonical_id:
        price = await oanda.get_price(body.canonical_id)

    chart_snapshots = None
    if body.mode == "deep_analysis" and body.canonical_id:
        chart_snapshots = await ChartVisionService().capture(body.canonical_id, body.timeframe)

    request = AnalysisRequest(
        canonical_id=body.canonical_id or "EUR_USD",
        timeframe=body.timeframe,
        mode=body.mode,
        user_message=body.message,
        chart_snapshots=chart_snapshots,
        price=price,
    )
    result = await orchestrator.run_analysis(request)

    artifacts = []
    if result.get("recommendation"):
        rec_data = result["recommendation"]
        rec_data = await _apply_gates(rec_data, body.canonical_id or "EUR_USD", body.timeframe, chart_snapshots)
        if rec_data:
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
                    gate_results=rec_data.get("gate_results", {}),
                )
            )

    if body.mode == "quick_scan":
        assistant_content = result.get("quick_scan_response", "Quick scan complete — not a tradeable recommendation.")
    elif result.get("published") and artifacts:
        assistant_content = "Deep analysis complete. Recommendation ready for review."
    elif result.get("error"):
        assistant_content = result["error"]
    else:
        assistant_content = "Analysis refused by validation gates."

    return {
        "result": result,
        "artifacts": artifacts,
        "assistant_content": assistant_content,
        "transcript": result.get("transcript", []),
    }


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

    db.add(ChatMessage(session_id=session_id, role="user", content=body.message, analysis_mode=body.mode))

    analysis = await _run_chat_analysis(body, db, session_id)

    db.add(
        ChatMessage(
            session_id=session_id,
            role="assistant",
            content=analysis["assistant_content"],
            artifacts=analysis["artifacts"] or None,
            analysis_mode=body.mode,
        )
    )

    return {
        "session_id": session_id,
        "message": analysis["assistant_content"],
        "artifacts": analysis["artifacts"],
        "transcript_available": bool(analysis["transcript"]),
    }


@router.post("/chat/stream")
async def stream_message(
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

    db.add(ChatMessage(session_id=session_id, role="user", content=body.message, analysis_mode=body.mode))
    await db.flush()

    async def event_generator():
        tools = build_tool_registry(db)
        orchestrator = TradingAgentOrchestrator(tools)
        oanda = OandaService()

        price = await oanda.get_price(body.canonical_id or "EUR_USD") if body.canonical_id else None
        chart_snapshots = None
        if body.mode == "deep_analysis" and body.canonical_id:
            chart_snapshots = await ChartVisionService().capture(body.canonical_id, body.timeframe)

        request = AnalysisRequest(
            canonical_id=body.canonical_id or "EUR_USD",
            timeframe=body.timeframe,
            mode=body.mode,
            user_message=body.message,
            chart_snapshots=chart_snapshots,
            price=price,
        )

        final_result = None
        async for event in orchestrator.run_analysis_stream(request):
            yield {"event": event.get("event", "progress"), "data": json.dumps(event)}
            if event.get("event") == "complete":
                final_result = event

        if final_result:
            artifacts = []
            assistant_content = final_result.get("quick_scan_response", "Analysis complete.")
            if final_result.get("recommendation"):
                rec_data = final_result["recommendation"]
                rec_data = await _apply_gates(
                    rec_data, body.canonical_id or "EUR_USD", body.timeframe, chart_snapshots
                )
                if rec_data:
                    rec = Recommendation(**rec_data)
                    db.add(rec)
                    await db.flush()
                    artifacts.append({"type": "recommendation_card", "data": {"id": rec.id, **rec_data}})
                    assistant_content = "Deep analysis complete. Recommendation ready for review."
                    db.add(
                        AgentRunLog(
                            session_id=session_id,
                            recommendation_id=rec.id,
                            analysis_mode=body.mode,
                            transcript=final_result.get("transcript", []),
                            gate_results=rec_data.get("gate_results", {}),
                        )
                    )

            db.add(
                ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=assistant_content,
                    artifacts=artifacts or None,
                    analysis_mode=body.mode,
                )
            )
            await db.commit()
            yield {
                "event": "saved",
                "data": json.dumps({"session_id": session_id, "artifacts": artifacts}),
            }

    return EventSourceResponse(event_generator())


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

    chart_snapshots = await ChartVisionService().capture(body.canonical_id, body.timeframe)
    if not chart_snapshots:
        raise HTTPException(503, "Chart vision unavailable")

    tools = build_tool_registry(db)
    orchestrator = TradingAgentOrchestrator(tools)
    oanda = OandaService()
    price = await oanda.get_price(body.canonical_id)

    request = AnalysisRequest(
        canonical_id=body.canonical_id,
        timeframe=body.timeframe,
        mode="deep_analysis",
        user_message="New Analysis",
        chart_snapshots=chart_snapshots,
        price=price,
    )
    result = await orchestrator.run_analysis(request)
    if not result.get("recommendation"):
        return {"published": False, "error": result.get("error", "Gates refused publication")}

    rec_data = await _apply_gates(result["recommendation"], body.canonical_id, body.timeframe, chart_snapshots)
    if not rec_data:
        return {"published": False, "error": "Validation gates refused publication"}

    rec = Recommendation(**rec_data)
    db.add(rec)
    await db.flush()
    db.add(
        AgentRunLog(
            recommendation_id=rec.id,
            analysis_mode="deep_analysis",
            transcript=result["transcript"],
            gate_results=rec_data.get("gate_results", {}),
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


async def _apply_gates(
    rec_data: dict,
    canonical_id: str,
    timeframe: str,
    chart_snapshots: Optional[dict],
) -> Optional[dict]:
    gates = ValidationGates()
    oanda = OandaService()
    price = await oanda.get_price(canonical_id)
    feed = await FeedHealthService().check_divergence(canonical_id)

    ctx = GateContext(
        canonical_id=canonical_id,
        timeframe=timeframe,
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
        chart_vision_ok=bool(chart_snapshots),
    )
    gate_results = gates.run_all(ctx)
    rec_data["gate_results"] = [
        {"gate": g.gate_name, "passed": g.passed, "reason": g.reason, "action": g.action}
        for g in gate_results
    ]
    return rec_data if gates.should_publish(gate_results) else None
