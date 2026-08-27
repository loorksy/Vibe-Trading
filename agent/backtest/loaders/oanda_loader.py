"""OANDA loader — primary forex/metals data source for analysis."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from backtest.loaders.base import cached_loader_fetch, validate_date_range
from backtest.loaders.registry import register
from src.providers.oanda.client import OandaClient, _canonical_to_oanda

logger = logging.getLogger(__name__)

_GRANULARITY_MAP = {
    "1m": "M1", "5m": "M5", "15m": "M15", "30m": "M30",
    "1H": "H1", "1h": "H1",
    "4H": "H4", "4h": "H4",
    "1D": "D1", "1d": "D",
    "1W": "W", "1w": "W",
}


@register
class DataLoader:
    name = "oanda"
    markets = frozenset({"forex"})

    def is_available(self) -> bool:
        return OandaClient().available or bool(OandaClient().api_token)

    def fetch(
        self,
        codes: list[str],
        start_date: str,
        end_date: str,
        interval: str = "1D",
    ) -> dict[str, pd.DataFrame]:
        validate_date_range(start_date, end_date)
        gran = _GRANULARITY_MAP.get(interval, "D")
        client = OandaClient()
        out: dict[str, pd.DataFrame] = {}
        for code in codes:
            df = cached_loader_fetch(
                self.name,
                code,
                start_date,
                end_date,
                interval,
                lambda: self._fetch_one(client, code, gran),
            )
            if df is not None and not df.empty:
                out[code] = df
        return out

    def _fetch_one(self, client: OandaClient, code: str, granularity: str) -> pd.DataFrame:
        rows = client.get_candles(code, granularity=granularity, count=5000)
        if not rows:
            return pd.DataFrame()
        frame = pd.DataFrame(rows)
        frame["trade_date"] = pd.to_datetime(frame["time"], utc=True)
        frame = frame.set_index("trade_date").sort_index()
        return frame[["open", "high", "low", "close", "volume"]]
