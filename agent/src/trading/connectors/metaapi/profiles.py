"""MetaApi connector profiles — execution and account status only."""

from __future__ import annotations

from src.trading.types import READ_CAPABILITIES, TradingProfile

METAAPI_PROFILES: tuple[TradingProfile, ...] = (
    TradingProfile(
        id="metaapi-live-readonly",
        connector="metaapi",
        label="MetaApi · Live Read-Only",
        environment="live",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES,
        readonly=True,
        config={"profile": "live-readonly"},
        notes=(
            "Reads account and positions through MetaApi. OANDA remains the sole "
            "source for analysis candles and prices."
        ),
    ),
    TradingProfile(
        id="metaapi-live-trade",
        connector="metaapi",
        label="MetaApi · Live Execution",
        environment="live",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES + ("orders.place.requires_mandate",),
        readonly=False,
        config={"profile": "live"},
        notes=(
            "Places orders via MetaApi. Execution is gated behind mandate and "
            "kill switch; analysis never routes through MetaApi."
        ),
    ),
)
