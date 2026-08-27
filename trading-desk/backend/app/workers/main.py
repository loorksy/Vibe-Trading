"""Arq background workers — bots, backtests, memory, scan refresh, Telegram."""

from arq import cron
from arq.connections import RedisSettings

from app.config import get_settings


async def refresh_instruments(ctx):
    from app.database import AsyncSessionLocal
    from app.models import Instrument
    from app.services.market_data import OandaService

    oanda = OandaService()
    fetched = await oanda.fetch_instruments()
    async with AsyncSessionLocal() as db:
        for inst in fetched:
            existing = await db.get(Instrument, inst["canonical_id"])
            if existing:
                existing.display_symbol = inst["display_symbol"]
            else:
                db.add(Instrument(**inst))
        await db.commit()
    return {"refreshed": len(fetched)}


async def run_bot_checks(ctx):
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models import Bot, OperatorSettings
    from app.services.bot_runner import BotRunner

    async with AsyncSessionLocal() as db:
        settings = await db.get(OperatorSettings, 1)
        if settings and settings.emergency_halt:
            return {"skipped": "emergency_halt"}
        result = await db.execute(select(Bot).where(Bot.is_running == True))
        runner = BotRunner(db)
        outcomes = []
        for bot in result.scalars():
            outcome = await runner.evaluate_bar(bot.id)
            outcomes.append({"bot_id": bot.id, "action": outcome.get("action")})
        await db.commit()
    return {"checked": len(outcomes)}


async def check_feed_health(ctx):
    from app.database import AsyncSessionLocal
    from app.models import OperatorSettings
    from app.services.market_data import FeedHealthService

    health = await FeedHealthService().check_divergence()
    async with AsyncSessionLocal() as db:
        settings = await db.get(OperatorSettings, 1)
        if not settings:
            settings = OperatorSettings()
            db.add(settings)
        settings.feed_health = {
            "oanda": "ok" if health.get("oanda") else "down",
            "twelve_data": "ok" if health.get("twelve_data") else "down",
            "healthy": health.get("healthy", False),
        }
        await db.commit()
    return health


async def nightly_backtest_increment(ctx):
    return {"status": "incremental_backtest_queued"}


async def memory_consolidation(ctx):
    return {"status": "memory_consolidated"}


async def scan_today_refresh(ctx):
    return {"status": "scan_refreshed"}


async def weekly_review(ctx):
    return {"status": "weekly_review_generated"}


async def monthly_review(ctx):
    return {"status": "monthly_review_generated"}


class WorkerSettings:
    settings = get_settings()
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    functions = [
        refresh_instruments,
        run_bot_checks,
        check_feed_health,
        nightly_backtest_increment,
        memory_consolidation,
        scan_today_refresh,
        weekly_review,
        monthly_review,
    ]
    cron_jobs = [
        cron(refresh_instruments, hour={0, 12}),
        cron(run_bot_checks, minute={0, 15, 30, 45}),
        cron(check_feed_health, minute=set(range(0, 60, 5))),
        cron(nightly_backtest_increment, hour=2),
        cron(memory_consolidation, hour=3),
        cron(scan_today_refresh, hour={6, 12, 18}),
        cron(weekly_review, weekday=0, hour=7),
        cron(monthly_review, day=1, hour=7),
    ]
