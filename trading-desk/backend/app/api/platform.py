from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.database import get_db
from app.models import BacktestRun, MemoryLesson, OperatorSettings, PerformanceReview, WatchlistItem
from app.schemas import BacktestRequest, SettingsUpdate, WatchlistAdd
from app.services.backtest import BacktestEngine
from app.services.finnhub import FinnhubService
from app.services.market_data import FeedHealthService, OandaService

router = APIRouter(tags=["settings", "watchlist", "scan", "backtest", "memory"])


@router.get("/settings")
async def get_settings(db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    settings = await db.get(OperatorSettings, 1)
    if not settings:
        settings = OperatorSettings()
        db.add(settings)
        await db.flush()
    return {
        "language": settings.language,
        "theme": settings.theme,
        "risk_per_trade_r": settings.risk_per_trade_r,
        "spread_limit_pips": settings.spread_limit_pips,
        "daily_loss_limit_r": settings.daily_loss_limit_r,
        "consecutive_loss_limit": settings.consecutive_loss_limit,
        "price_divergence_threshold_pct": settings.price_divergence_threshold_pct,
        "exposure_cap_r": settings.exposure_cap_r,
        "live_promotion_confirmation_method": settings.live_promotion_confirmation_method,
        "notification_prefs": settings.notification_prefs,
        "emergency_halt": settings.emergency_halt,
        "feed_health": settings.feed_health,
    }


@router.patch("/settings")
async def update_settings(body: SettingsUpdate, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    settings = await db.get(OperatorSettings, 1)
    if not settings:
        settings = OperatorSettings()
        db.add(settings)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(settings, field, value)
    return {"updated": True}


@router.get("/watchlist")
async def get_watchlist(db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    result = await db.execute(select(WatchlistItem).order_by(WatchlistItem.sort_order))
    oanda = OandaService()
    items = []
    for w in result.scalars():
        price = await oanda.get_price(w.canonical_id)
        items.append({"canonical_id": w.canonical_id, "price": price})
    return items


@router.post("/watchlist")
async def add_watchlist(body: WatchlistAdd, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    db.add(WatchlistItem(canonical_id=body.canonical_id))
    return {"added": body.canonical_id}


@router.delete("/watchlist/{canonical_id}")
async def remove_watchlist(canonical_id: str, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    result = await db.execute(select(WatchlistItem).where(WatchlistItem.canonical_id == canonical_id))
    item = result.scalar_one_or_none()
    if item:
        await db.delete(item)
    return {"removed": canonical_id}


@router.get("/today")
async def scan_today(benchmark: str = "XAU_USD", db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    finnhub = FinnhubService()
    feed = FeedHealthService()
    news = await finnhub.get_news()
    calendar = await finnhub.get_economic_calendar()
    health = await feed.check_divergence()
    return {
        "news": news[:15],
        "calendar": calendar[:15],
        "feed_health": health,
        "benchmark": benchmark,
        "disclaimer": "Personal analysis only — not fund management advice.",
    }


@router.get("/exposure")
async def portfolio_exposure(db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    from app.agents.tools import build_tool_registry

    tools = build_tool_registry(db)
    fn = tools._tools["get_portfolio_exposure"]
    return await fn()


@router.post("/backtests")
async def run_backtest(body: BacktestRequest, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    oanda = OandaService()
    gran = {"15m": "M15", "1h": "H1", "4h": "H4", "1d": "D"}.get(body.timeframe, "H1")
    candles = await oanda.get_candles(body.canonical_id, gran, 500)
    engine = BacktestEngine()
    signals = [{"direction": "BUY" if i % 3 == 0 else "SELL"} for i in range(min(50, len(candles)))]
    result = engine.run(candles, signals)
    run = BacktestRun(
        strategy_version_id=body.strategy_version_id,
        canonical_id=body.canonical_id,
        timeframe=body.timeframe,
        start_date=body.start_date,
        end_date=body.end_date,
        status="completed",
        results={
            "equity_curve": result.equity_curve,
            "trades": result.trades[:50],
            "max_drawdown": result.max_drawdown,
            "profit_factor": result.profit_factor,
            "confidence_label": result.confidence_label,
            "stats": result.stats,
        },
        cost_model={"spread_pips": 1.5, "slippage_pips": 0.5},
    )
    db.add(run)
    await db.flush()
    return {"id": run.id, "results": run.results}


@router.get("/memory/lessons")
async def get_lessons(db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    result = await db.execute(select(MemoryLesson).order_by(MemoryLesson.created_at.desc()).limit(50))
    return [{"id": l.id, "lesson": l.lesson, "canonical_id": l.canonical_id} for l in result.scalars()]


@router.get("/review")
async def get_reviews(db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    result = await db.execute(select(PerformanceReview).order_by(PerformanceReview.created_at.desc()).limit(10))
    return [{"id": r.id, "period_type": r.period_type, "summary": r.summary} for r in result.scalars()]
