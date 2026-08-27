from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.database import get_db
from app.services.market_data import FeedHealthService
from app.services.metaapi import MetaApiService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    checks = {"api": "ok", "database": "unknown", "redis": "unknown", "oanda": "unknown", "metaapi": "unknown"}

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    try:
        import redis
        from app.config import get_settings
        r = redis.from_url(get_settings().redis_url)
        r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    feed = await FeedHealthService().check_divergence()
    checks["oanda"] = "ok" if feed.get("oanda") else "unavailable"
    checks["twelve_data"] = "ok" if feed.get("twelve_data") else "unavailable"
    checks["feed_healthy"] = feed.get("healthy", False)

    meta = MetaApiService()
    checks["metaapi"] = "configured" if meta._token else "not_configured"

    status = "healthy" if checks["database"] == "ok" else "degraded"
    return {"status": status, "checks": checks}
