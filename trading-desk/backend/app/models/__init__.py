import enum
from datetime import datetime
from typing import Optional
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid4())


class Direction(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class PlanType(str, enum.Enum):
    IMMEDIATE = "immediate"
    ANTICIPATORY = "anticipatory"
    CONDITIONAL = "conditional"


class ExecutionStatus(str, enum.Enum):
    ACTIVE_NOW = "active_now"
    AWAITING_ACTIVATION = "awaiting_activation"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    BLOCKED = "blocked"


class FillRule(str, enum.Enum):
    MARKET_PRICE = "market_price"
    LEVEL_TOUCH = "level_touch"
    CONFIRMATION_CANDLE_CLOSE = "confirmation_candle_close"
    RETURN_TO_ZONE = "return_to_zone"


class AnalysisMode(str, enum.Enum):
    QUICK_SCAN = "quick_scan"
    DEEP_ANALYSIS = "deep_analysis"


class BotState(str, enum.Enum):
    STOPPED = "stopped"
    DEMO = "demo"
    LIVE = "live"


class Instrument(Base):
    __tablename__ = "instruments"

    canonical_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    display_symbol: Mapped[str] = mapped_column(String(32), index=True)
    asset_class: Mapped[str] = mapped_column(String(64))
    tradable: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BrokerAccount(Base):
    __tablename__ = "broker_accounts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(128))
    account_type: Mapped[str] = mapped_column(String(16))  # demo | live
    metaapi_account_id: Mapped[str] = mapped_column(String(128))
    broker_server: Mapped[str] = mapped_column(String(256))
    encrypted_token: Mapped[str] = mapped_column(Text)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    last_health_check: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BrokerSymbolAlias(Base):
    __tablename__ = "broker_symbol_aliases"
    __table_args__ = (UniqueConstraint("account_id", "canonical_id"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    account_id: Mapped[str] = mapped_column(ForeignKey("broker_accounts.id", ondelete="CASCADE"))
    canonical_id: Mapped[str] = mapped_column(ForeignKey("instruments.canonical_id"))
    execution_symbol: Mapped[str] = mapped_column(String(64))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    canonical_id: Mapped[str] = mapped_column(ForeignKey("instruments.canonical_id"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    canonical_id: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[str] = mapped_column(String(8))
    direction: Mapped[str] = mapped_column(Enum(Direction, values_callable=lambda x: [e.value for e in x]))
    analytical_bias: Mapped[str] = mapped_column(Enum(Direction, values_callable=lambda x: [e.value for e in x]))
    plan_type: Mapped[str] = mapped_column(Enum(PlanType, values_callable=lambda x: [e.value for e in x]))
    execution_status: Mapped[str] = mapped_column(Enum(ExecutionStatus, values_callable=lambda x: [e.value for e in x]))
    fill_rule: Mapped[str] = mapped_column(Enum(FillRule, values_callable=lambda x: [e.value for e in x]))
    entry_zone_low: Mapped[float] = mapped_column(Float)
    entry_zone_high: Mapped[float] = mapped_column(Float)
    preferred_entry: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profits: Mapped[dict] = mapped_column(JSON)  # [{level, price, r_multiple}]
    invalidation_rule: Mapped[str] = mapped_column(Text)
    activation_rule: Mapped[Optional[str]] = mapped_column(Text)
    activation_condition: Mapped[Optional[str]] = mapped_column(Text)
    validity_candles: Mapped[int] = mapped_column(Integer)
    analysis_mode: Mapped[str] = mapped_column(Enum(AnalysisMode, values_callable=lambda x: [e.value for e in x]))
    confidence_label: Mapped[str] = mapped_column(String(64))  # percentage or "Insufficient data"
    similar_past_cases: Mapped[dict] = mapped_column(JSON, default=dict)
    gate_results: Mapped[dict] = mapped_column(JSON, default=dict)
    chart_snapshots: Mapped[dict] = mapped_column(JSON, default=dict)
    strategy_id: Mapped[Optional[str]] = mapped_column(String(64))
    backtest_stats: Mapped[Optional[dict]] = mapped_column(JSON)
    outcome: Mapped[Optional[str]] = mapped_column(String(32))  # tp1, tp2, tp3, sl, expired
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Execution(Base):
    """Separate from recommendations — real broker fills only."""

    __tablename__ = "executions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    recommendation_id: Mapped[Optional[str]] = mapped_column(ForeignKey("recommendations.id"))
    bot_id: Mapped[Optional[str]] = mapped_column(ForeignKey("bots.id"))
    account_id: Mapped[str] = mapped_column(ForeignKey("broker_accounts.id"))
    canonical_id: Mapped[str] = mapped_column(String(32))
    execution_symbol: Mapped[str] = mapped_column(String(64))
    direction: Mapped[str] = mapped_column(String(8))
    lot_size: Mapped[float] = mapped_column(Float)
    entry_price: Mapped[Optional[float]] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profits: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    broker_order_id: Mapped[Optional[str]] = mapped_column(String(128))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    rationale_id: Mapped[Optional[str]] = mapped_column(ForeignKey("trade_rationales.id"))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text)
    active_version_id: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    versions: Mapped[list["StrategyVersion"]] = relationship(back_populates="strategy")


class StrategyVersion(Base):
    __tablename__ = "strategy_versions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id", ondelete="CASCADE"))
    version_number: Mapped[int] = mapped_column(Integer)
    code: Mapped[str] = mapped_column(Text)
    allowed_instruments: Mapped[dict] = mapped_column(JSON, default=list)
    timeframe: Mapped[str] = mapped_column(String(8))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    strategy: Mapped["Strategy"] = relationship(back_populates="versions")


class Bot(Base):
    __tablename__ = "bots"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(128))
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id"))
    active_version_id: Mapped[str] = mapped_column(String(64))
    canonical_id: Mapped[str] = mapped_column(String(32))
    timeframe: Mapped[str] = mapped_column(String(8))
    account_id: Mapped[Optional[str]] = mapped_column(ForeignKey("broker_accounts.id"))
    state: Mapped[str] = mapped_column(Enum(BotState, values_callable=lambda x: [e.value for e in x]), default=BotState.STOPPED.value)
    risk_per_trade_r: Mapped[float] = mapped_column(Float, default=1.0)
    spread_limit_pips: Mapped[float] = mapped_column(Float, default=3.0)
    open_position_cap: Mapped[int] = mapped_column(Integer, default=1)
    is_running: Mapped[bool] = mapped_column(Boolean, default=False)
    source_recommendation_id: Mapped[Optional[str]] = mapped_column(ForeignKey("recommendations.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TradeRationale(Base):
    __tablename__ = "trade_rationales"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    bot_id: Mapped[str] = mapped_column(ForeignKey("bots.id"))
    rules_fired: Mapped[dict] = mapped_column(JSON)
    snapshot: Mapped[dict] = mapped_column(JSON)
    why_this_bar: Mapped[str] = mapped_column(Text)
    behavior_fit: Mapped[str] = mapped_column(Text)
    risk_r: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profits: Mapped[dict] = mapped_column(JSON)
    gates_passed: Mapped[dict] = mapped_column(JSON)
    veto_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentRunLog(Base):
    __tablename__ = "agent_run_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    session_id: Mapped[Optional[str]] = mapped_column(String(64))
    recommendation_id: Mapped[Optional[str]] = mapped_column(ForeignKey("recommendations.id"))
    analysis_mode: Mapped[str] = mapped_column(String(32))
    transcript: Mapped[dict] = mapped_column(JSON)
    gate_results: Mapped[dict] = mapped_column(JSON, default=dict)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    title: Mapped[Optional[str]] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    artifacts: Mapped[Optional[dict]] = mapped_column(JSON)
    analysis_mode: Mapped[Optional[str]] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    session: Mapped["ChatSession"] = relationship(back_populates="messages")


class AgentMemory(Base):
    __tablename__ = "agent_memory"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    recommendation_id: Mapped[Optional[str]] = mapped_column(ForeignKey("recommendations.id"))
    canonical_id: Mapped[str] = mapped_column(String(32), index=True)
    context_text: Mapped[str] = mapped_column(Text)
    outcome: Mapped[str] = mapped_column(String(32))
    embedding = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MemoryLesson(Base):
    __tablename__ = "memory_lessons"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    canonical_id: Mapped[Optional[str]] = mapped_column(String(32))
    strategy_id: Mapped[Optional[str]] = mapped_column(String(64))
    lesson: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    strategy_version_id: Mapped[str] = mapped_column(String(64))
    canonical_id: Mapped[str] = mapped_column(String(32))
    timeframe: Mapped[str] = mapped_column(String(8))
    start_date: Mapped[str] = mapped_column(String(16))
    end_date: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    results: Mapped[Optional[dict]] = mapped_column(JSON)
    cost_model: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OperatorSettings(Base):
    __tablename__ = "operator_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    language: Mapped[str] = mapped_column(String(8), default="en")
    theme: Mapped[str] = mapped_column(String(16), default="dark")
    risk_per_trade_r: Mapped[float] = mapped_column(Float, default=1.0)
    spread_limit_pips: Mapped[float] = mapped_column(Float, default=3.0)
    daily_loss_limit_r: Mapped[float] = mapped_column(Float, default=5.0)
    consecutive_loss_limit: Mapped[int] = mapped_column(Integer, default=3)
    price_divergence_threshold_pct: Mapped[float] = mapped_column(Float, default=0.15)
    exposure_cap_r: Mapped[Optional[float]] = mapped_column(Float)
    live_promotion_confirmation_method: Mapped[str] = mapped_column(String(16), default="pin")
    live_promotion_pin_hash: Mapped[Optional[str]] = mapped_column(String(256))
    notification_prefs: Mapped[dict] = mapped_column(JSON, default=dict)
    telegram_chat_id: Mapped[Optional[str]] = mapped_column(String(64))
    telegram_link_code: Mapped[Optional[str]] = mapped_column(String(16))
    emergency_halt: Mapped[bool] = mapped_column(Boolean, default=False)
    feed_health: Mapped[dict] = mapped_column(JSON, default=lambda: {"oanda": "unknown", "twelve_data": "unknown"})


class NewsCache(Base):
    __tablename__ = "news_cache"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(String(32))
    data: Mapped[dict] = mapped_column(JSON)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PerformanceReview(Base):
    __tablename__ = "performance_reviews"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    period_type: Mapped[str] = mapped_column(String(16))  # weekly | monthly
    period_start: Mapped[str] = mapped_column(String(16))
    period_end: Mapped[str] = mapped_column(String(16))
    summary: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
