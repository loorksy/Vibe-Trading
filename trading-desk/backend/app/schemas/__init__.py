from typing import Any, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class InstrumentOut(BaseModel):
    canonical_id: str
    display_symbol: str
    asset_class: str
    tradable: bool


class RecommendationCreate(BaseModel):
    canonical_id: str
    timeframe: str = "1h"
    mode: str = "deep_analysis"


class RecommendationOut(BaseModel):
    id: str
    canonical_id: str
    timeframe: str
    direction: str
    analytical_bias: str
    plan_type: str
    execution_status: str
    fill_rule: str
    entry_zone_low: float
    entry_zone_high: float
    preferred_entry: float
    stop_loss: float
    take_profits: list[dict[str, Any]]
    invalidation_rule: str
    activation_rule: Optional[str] = None
    activation_condition: Optional[str] = None
    validity_candles: int
    analysis_mode: str
    confidence_label: str
    similar_past_cases: dict[str, Any]
    gate_results: dict[str, Any]
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class ExecuteTradeRequest(BaseModel):
    recommendation_id: str
    account_id: str
    lot_size: float


class BrokerConnectRequest(BaseModel):
    name: str
    account_type: str
    metaapi_account_id: str
    broker_server: str
    token: str


class SymbolAliasRequest(BaseModel):
    account_id: str
    canonical_id: str
    execution_symbol: str


class ChatMessageRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    mode: str = "quick_scan"
    canonical_id: Optional[str] = None
    timeframe: str = "1h"


class BotActivateRequest(BaseModel):
    bot_id: str
    canonical_id: str
    timeframe: str
    account_id: str
    risk_per_trade_r: float = 1.0
    spread_limit_pips: float = 3.0
    open_position_cap: int = 1


class PromoteLiveRequest(BaseModel):
    bot_id: str
    confirmation: str


class BacktestRequest(BaseModel):
    strategy_version_id: str
    canonical_id: str
    timeframe: str
    start_date: str
    end_date: str


class SettingsUpdate(BaseModel):
    language: Optional[str] = None
    theme: Optional[str] = None
    risk_per_trade_r: Optional[float] = None
    spread_limit_pips: Optional[float] = None
    daily_loss_limit_r: Optional[float] = None
    consecutive_loss_limit: Optional[int] = None
    price_divergence_threshold_pct: Optional[float] = None
    exposure_cap_r: Optional[float] = None
    live_promotion_confirmation_method: Optional[str] = None
    notification_prefs: Optional[dict[str, Any]] = None


class WatchlistAdd(BaseModel):
    canonical_id: str
