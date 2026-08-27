from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.database import get_db
from app.models import Instrument
from app.schemas import InstrumentOut
from app.services.market_data import FeedHealthService, OandaService

router = APIRouter(prefix="/instruments", tags=["instruments"])


@router.get("", response_model=list[InstrumentOut])
async def list_instruments(
    q: str = "",
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(select(Instrument).order_by(Instrument.display_symbol))
    items = result.scalars().all()
    if not items:
        oanda = OandaService()
        fetched = await oanda.fetch_instruments()
        for inst in fetched:
            db.add(Instrument(**inst))
        await db.flush()
        result = await db.execute(select(Instrument).order_by(Instrument.display_symbol))
        items = result.scalars().all()
    if q:
        q_lower = q.lower()
        items = [i for i in items if q_lower in i.display_symbol.lower() or q_lower in i.canonical_id.lower()]
    return items


@router.post("/refresh")
async def refresh_instruments(db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    oanda = OandaService()
    fetched = await oanda.fetch_instruments()
    for inst in fetched:
        existing = await db.get(Instrument, inst["canonical_id"])
        if existing:
            existing.display_symbol = inst["display_symbol"]
            existing.asset_class = inst["asset_class"]
            existing.tradable = inst["tradable"]
        else:
            db.add(Instrument(**inst))
    return {"refreshed": len(fetched)}


@router.get("/{canonical_id}/candles")
async def get_candles(
    canonical_id: str,
    timeframe: str = "1h",
    count: int = 500,
    _: str = Depends(get_current_user),
):
    oanda = OandaService()
    granularity = {"1m": "M1", "5m": "M5", "15m": "M15", "1h": "H1", "4h": "H4", "1d": "D"}.get(timeframe, "H1")
    candles = await oanda.get_candles(canonical_id, granularity, count)
    return {"canonical_id": canonical_id, "timeframe": timeframe, "candles": candles, "source": "oanda"}


@router.get("/{canonical_id}/price")
async def get_price(canonical_id: str, _: str = Depends(get_current_user)):
    oanda = OandaService()
    price = await oanda.get_price(canonical_id)
    health = await FeedHealthService().check_divergence(canonical_id)
    return {"price": price, "feed_health": health}
