"""OANDA v20 REST client for instruments, candles, and live pricing."""

from __future__ import annotations

import logging
import os
from typing import Any

from backtest.loaders._http import throttled_get_json

logger = logging.getLogger(__name__)

_HOST_KEY = "oanda"
_DEFAULT_API_URL = "https://api-fxpractice.oanda.com"


def _canonical_to_oanda(code: str) -> str:
    upper = code.strip().upper().replace("/", "_").replace(".FX", "")
    if "_" in upper:
        return upper
    if len(upper) == 6:
        return f"{upper[:3]}_{upper[3:]}"
    return upper


def _oanda_to_display(canonical: str) -> str:
    return canonical.replace("_", "")


class OandaClient:
    """Read-only OANDA market data — sole source for analysis candles/prices."""

    def __init__(self) -> None:
        self.api_token = os.environ.get("OANDA_API_TOKEN", "")
        self.account_id = os.environ.get("OANDA_ACCOUNT_ID", "")
        self.api_url = os.environ.get("OANDA_API_URL", _DEFAULT_API_URL).rstrip("/")

    @property
    def available(self) -> bool:
        return bool(self.api_token and self.account_id)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def list_instruments(self) -> list[dict[str, Any]]:
        if not self.available:
            return self._demo_instruments()
        url = f"{self.api_url}/v3/accounts/{self.account_id}/instruments"
        data = throttled_get_json(url, headers=self._headers(), host_key=_HOST_KEY)
        return [
            {
                "canonical_id": item["name"],
                "display_symbol": _oanda_to_display(item["name"]),
                "asset_class": item.get("type", "CURRENCY"),
                "tradable": True,
            }
            for item in data.get("instruments", [])
        ]

    def get_candles(
        self,
        code: str,
        granularity: str = "H1",
        count: int = 500,
    ) -> list[dict[str, Any]]:
        if not self.api_token:
            return []
        canonical = _canonical_to_oanda(code)
        url = (
            f"{self.api_url}/v3/instruments/{canonical}/candles"
            f"?granularity={granularity}&count={count}&price=M"
        )
        data = throttled_get_json(url, headers=self._headers(), host_key=_HOST_KEY)
        rows: list[dict[str, Any]] = []
        for candle in data.get("candles", []):
            if not candle.get("complete"):
                continue
            mid = candle["mid"]
            rows.append(
                {
                    "time": candle["time"],
                    "open": float(mid["o"]),
                    "high": float(mid["h"]),
                    "low": float(mid["l"]),
                    "close": float(mid["c"]),
                    "volume": int(candle.get("volume", 0)),
                }
            )
        return rows

    def get_price(self, code: str) -> dict[str, float] | None:
        if not self.available:
            return None
        canonical = _canonical_to_oanda(code)
        url = f"{self.api_url}/v3/accounts/{self.account_id}/pricing"
        data = throttled_get_json(
            url,
            params={"instruments": canonical},
            headers=self._headers(),
            host_key=_HOST_KEY,
        )
        prices = data.get("prices", [])
        if not prices:
            return None
        p = prices[0]
        bid = float(p["bids"][0]["price"])
        ask = float(p["asks"][0]["price"])
        return {"bid": bid, "ask": ask, "mid": (bid + ask) / 2, "spread": ask - bid}

    def _demo_instruments(self) -> list[dict[str, Any]]:
        pairs = [
            ("EUR_USD", "EURUSD", "CURRENCY"),
            ("GBP_USD", "GBPUSD", "CURRENCY"),
            ("USD_JPY", "USDJPY", "CURRENCY"),
            ("XAU_USD", "XAUUSD", "METAL"),
            ("AUD_USD", "AUDUSD", "CURRENCY"),
        ]
        return [
            {"canonical_id": c, "display_symbol": d, "asset_class": a, "tradable": True}
            for c, d, a in pairs
        ]
