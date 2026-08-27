from typing import Any, Optional

import httpx

from app.config import get_settings


class OandaService:
    """Primary market data source — sole source for analysis, charts, indicators."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.oanda_api_token}",
            "Content-Type": "application/json",
        }

    async def fetch_instruments(self) -> list[dict[str, Any]]:
        if not self.settings.oanda_api_token or not self.settings.oanda_account_id:
            return self._demo_instruments()
        url = f"{self.settings.oanda_api_url}/v3/accounts/{self.settings.oanda_account_id}/instruments"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
        instruments = []
        for item in data.get("instruments", []):
            name = item["name"]
            instruments.append(
                {
                    "canonical_id": name,
                    "display_symbol": name.replace("_", ""),
                    "asset_class": item.get("type", "CURRENCY"),
                    "tradable": True,
                }
            )
        return instruments

    async def get_candles(
        self,
        canonical_id: str,
        granularity: str = "H1",
        count: int = 500,
    ) -> list[dict[str, Any]]:
        if not self.settings.oanda_api_token:
            return []
        url = (
            f"{self.settings.oanda_api_url}/v3/instruments/{canonical_id}/candles"
            f"?granularity={granularity}&count={count}&price=M"
        )
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
        candles = []
        for c in data.get("candles", []):
            if not c.get("complete"):
                continue
            mid = c["mid"]
            candles.append(
                {
                    "time": c["time"],
                    "open": float(mid["o"]),
                    "high": float(mid["h"]),
                    "low": float(mid["l"]),
                    "close": float(mid["c"]),
                    "volume": int(c.get("volume", 0)),
                }
            )
        return candles

    async def get_price(self, canonical_id: str) -> Optional[dict[str, float]]:
        if not self.settings.oanda_api_token:
            return None
        url = f"{self.settings.oanda_api_url}/v3/accounts/{self.settings.oanda_account_id}/pricing"
        params = {"instruments": canonical_id}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=self.headers, params=params)
            resp.raise_for_status()
            data = resp.json()
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
            ("USD_CAD", "USDCAD", "CURRENCY"),
            ("NZD_USD", "NZDUSD", "CURRENCY"),
            ("EUR_GBP", "EURGBP", "CURRENCY"),
            ("EUR_JPY", "EURJPY", "CURRENCY"),
            ("GBP_JPY", "GBPJPY", "CURRENCY"),
            ("USD_CHF", "USDCHF", "CURRENCY"),
        ]
        return [
            {"canonical_id": c, "display_symbol": d, "asset_class": a, "tradable": True}
            for c, d, a in pairs
        ]


class TwelveDataService:
    """Fallback cross-check only — never used for indicator computation."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def get_price(self, canonical_id: str) -> Optional[float]:
        if not self.settings.twelve_data_api_key:
            return None
        symbol = canonical_id.replace("_", "/")
        url = "https://api.twelvedata.com/price"
        params = {"symbol": symbol, "apikey": self.settings.twelve_data_api_key}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return None
            data = resp.json()
        price = data.get("price")
        return float(price) if price else None


class FeedHealthService:
    def __init__(self) -> None:
        self.oanda = OandaService()
        self.twelve = TwelveDataService()
        self.settings = get_settings()

    async def check_divergence(self, canonical_id: str = "EUR_USD") -> dict[str, Any]:
        oanda = await self.oanda.get_price(canonical_id)
        twelve = await self.twelve.get_price(canonical_id)
        if oanda is None:
            return {"healthy": False, "reason": "OANDA unavailable", "oanda": None, "twelve_data": twelve}
        if twelve is None:
            return {"healthy": True, "reason": "OANDA ok, Twelve Data unavailable", "oanda": oanda["mid"], "twelve_data": None}
        divergence = abs(oanda["mid"] - twelve) / oanda["mid"] * 100
        healthy = divergence <= self.settings.price_divergence_threshold_pct
        return {
            "healthy": healthy,
            "divergence_pct": divergence,
            "oanda": oanda["mid"],
            "twelve_data": twelve,
            "reason": "ok" if healthy else "Price data unreliable",
        }
