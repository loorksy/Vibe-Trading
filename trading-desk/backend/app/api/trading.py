from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.crypto import encrypt_value
from app.database import get_db
from app.models import Bot, BrokerAccount, BrokerSymbolAlias, Execution, OperatorSettings, Strategy, StrategyVersion
from app.schemas import BotActivateRequest, BrokerConnectRequest, ExecuteTradeRequest, PromoteLiveRequest, SymbolAliasRequest
from app.services.metaapi import MetaApiService

router = APIRouter(tags=["account", "execution", "bots"])


@router.post("/account/connect")
async def connect_broker(body: BrokerConnectRequest, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    meta = MetaApiService(body.token)
    test = await meta.test_connection(body.metaapi_account_id)
    account = BrokerAccount(
        name=body.name,
        account_type=body.account_type,
        metaapi_account_id=body.metaapi_account_id,
        broker_server=body.broker_server,
        encrypted_token=encrypt_value(body.token),
        is_connected=test.get("connected", False),
    )
    db.add(account)
    await db.flush()
    return {"id": account.id, "connected": account.is_connected, "test": test}


@router.get("/account/accounts")
async def list_accounts(db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    result = await db.execute(select(BrokerAccount))
    return [
        {
            "id": a.id,
            "name": a.name,
            "account_type": a.account_type,
            "is_connected": a.is_connected,
            "broker_server": a.broker_server,
        }
        for a in result.scalars()
    ]


@router.post("/account/aliases")
async def save_alias(body: SymbolAliasRequest, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    account = await db.get(BrokerAccount, body.account_id)
    if not account:
        raise HTTPException(404, "Account not found")
    meta = MetaApiService(account.encrypted_token)
    resolved = await meta.resolve_symbol(account.metaapi_account_id, body.execution_symbol)
    alias = BrokerSymbolAlias(
        account_id=body.account_id,
        canonical_id=body.canonical_id,
        execution_symbol=body.execution_symbol,
        verified=resolved.get("resolved", False),
    )
    db.add(alias)
    await db.flush()
    return {"id": alias.id, "verified": alias.verified, "resolve": resolved}


@router.get("/account/aliases/{account_id}")
async def list_aliases(account_id: str, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    result = await db.execute(select(BrokerSymbolAlias).where(BrokerSymbolAlias.account_id == account_id))
    return [
        {"canonical_id": a.canonical_id, "execution_symbol": a.execution_symbol, "verified": a.verified}
        for a in result.scalars()
    ]


@router.post("/executions")
async def execute_trade(body: ExecuteTradeRequest, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    settings = await db.get(OperatorSettings, 1)
    if settings and settings.emergency_halt:
        raise HTTPException(503, "Emergency halt active")

    from app.models import Recommendation

    rec = await db.get(Recommendation, body.recommendation_id)
    if not rec:
        raise HTTPException(404, "Recommendation not found")

    account = await db.get(BrokerAccount, body.account_id)
    if not account:
        raise HTTPException(404, "Account not found")

    alias_result = await db.execute(
        select(BrokerSymbolAlias).where(
            BrokerSymbolAlias.account_id == body.account_id,
            BrokerSymbolAlias.canonical_id == rec.canonical_id,
        )
    )
    alias = alias_result.scalar_one_or_none()
    if not alias:
        raise HTTPException(400, "Broker symbol not mapped")

    meta = MetaApiService(account.encrypted_token)
    tp1 = rec.take_profits[0]["price"] if rec.take_profits else None
    result = await meta.place_order(
        account.metaapi_account_id,
        alias.execution_symbol,
        rec.direction,
        body.lot_size,
        rec.stop_loss,
        tp1,
        client_id=f"rec-{rec.id}",
    )

    execution = Execution(
        recommendation_id=rec.id,
        account_id=body.account_id,
        canonical_id=rec.canonical_id,
        execution_symbol=alias.execution_symbol,
        direction=rec.direction,
        lot_size=body.lot_size,
        stop_loss=rec.stop_loss,
        take_profits=rec.take_profits,
        status="submitted" if result.get("status") == "submitted" else "error",
        broker_order_id=result.get("data", {}).get("orderId"),
        error_message=result.get("error"),
        is_demo=account.account_type == "demo",
    )
    db.add(execution)
    await db.flush()
    return {"execution_id": execution.id, "result": result}


@router.get("/executions")
async def list_executions(db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    result = await db.execute(select(Execution).order_by(Execution.created_at.desc()).limit(100))
    return [
        {
            "id": e.id,
            "canonical_id": e.canonical_id,
            "direction": e.direction,
            "lot_size": e.lot_size,
            "status": e.status,
            "is_demo": e.is_demo,
            "created_at": e.created_at.isoformat(),
        }
        for e in result.scalars()
    ]


@router.get("/bots")
async def list_bots(db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    result = await db.execute(select(Bot))
    return [
        {
            "id": b.id,
            "name": b.name,
            "canonical_id": b.canonical_id,
            "timeframe": b.timeframe,
            "state": b.state,
            "is_running": b.is_running,
            "active_version_id": b.active_version_id,
        }
        for b in result.scalars()
    ]


@router.post("/bots/{bot_id}/activate")
async def activate_bot(bot_id: str, body: BotActivateRequest, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    bot = await db.get(Bot, bot_id)
    if not bot:
        raise HTTPException(404, "Bot not found")
    bot.canonical_id = body.canonical_id
    bot.timeframe = body.timeframe
    bot.account_id = body.account_id
    bot.risk_per_trade_r = body.risk_per_trade_r
    bot.spread_limit_pips = body.spread_limit_pips
    bot.open_position_cap = body.open_position_cap
    bot.is_running = True
    bot.state = "demo"
    return {"id": bot.id, "is_running": True, "state": bot.state}


@router.post("/bots/{bot_id}/stop")
async def stop_bot(bot_id: str, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    bot = await db.get(Bot, bot_id)
    if not bot:
        raise HTTPException(404, "Bot not found")
    bot.is_running = False
    return {"id": bot.id, "is_running": False}


@router.post("/bots/stop-all")
async def stop_all_bots(db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    settings = await db.get(OperatorSettings, 1)
    if not settings:
        settings = OperatorSettings()
        db.add(settings)
    settings.emergency_halt = True
    result = await db.execute(select(Bot).where(Bot.is_running == True))
    for bot in result.scalars():
        bot.is_running = False
    return {"halted": True, "bots_stopped": True}


@router.post("/bots/{bot_id}/promote-live")
async def promote_live(bot_id: str, body: PromoteLiveRequest, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    bot = await db.get(Bot, bot_id)
    if not bot:
        raise HTTPException(404, "Bot not found")
    settings = await db.get(OperatorSettings, 1)
    method = settings.live_promotion_confirmation_method if settings else "pin"
    if method == "symbol" and body.confirmation != bot.canonical_id:
        raise HTTPException(400, "Confirmation symbol mismatch")
  # PIN check would verify hash here
    bot.state = "live"
    return {"id": bot.id, "state": "live"}


@router.post("/recommendations/{rec_id}/convert-bot")
async def convert_to_bot(rec_id: str, db: AsyncSession = Depends(get_db), _: str = Depends(get_current_user)):
    from app.models import Recommendation

    rec = await db.get(Recommendation, rec_id)
    if not rec:
        raise HTTPException(404, "Recommendation not found")
    strategy = Strategy(name=f"Rec-{rec.canonical_id}", description=rec.invalidation_rule)
    db.add(strategy)
    await db.flush()
    version = StrategyVersion(
        strategy_id=strategy.id,
        version_number=1,
        code="# Generated from recommendation — exact entry/stop/targets locked",
        allowed_instruments=[rec.canonical_id],
        timeframe=rec.timeframe,
    )
    db.add(version)
    await db.flush()
    strategy.active_version_id = version.id
    bot = Bot(
        name=f"Bot-{rec.canonical_id}",
        strategy_id=strategy.id,
        active_version_id=version.id,
        canonical_id=rec.canonical_id,
        timeframe=rec.timeframe,
        source_recommendation_id=rec.id,
    )
    db.add(bot)
    await db.flush()
    return {"bot_id": bot.id, "strategy_id": strategy.id}
