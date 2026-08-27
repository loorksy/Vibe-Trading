from typing import Any, Optional

import httpx

from app.config import get_settings
from app.core.crypto import decrypt_value


class MetaApiService:
    """Execution and account status ONLY — never for analysis candles/prices."""

    BASE_URL = "https://mt-client-api-v1.london.agiliumtrade.ai"

    def __init__(self, encrypted_token: Optional[str] = None) -> None:
        self.settings = get_settings()
        self._token = decrypt_value(encrypted_token) if encrypted_token else self.settings.metaapi_token

    @property
    def headers(self) -> dict[str, str]:
        return {"auth-token": self._token, "Content-Type": "application/json"}

    async def test_connection(self, account_id: str) -> dict[str, Any]:
        if not self._token:
            return {"connected": False, "error": "MetaApi token not configured"}
        url = f"{self.BASE_URL}/users/current/accounts/{account_id}/account-information"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, headers=self.headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "connected": True,
                        "balance": data.get("balance"),
                        "equity": data.get("equity"),
                        "margin": data.get("margin"),
                    }
                return {"connected": False, "error": resp.text}
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def resolve_symbol(self, account_id: str, execution_symbol: str) -> dict[str, Any]:
        url = f"{self.BASE_URL}/users/current/accounts/{account_id}/symbols"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=self.headers)
            if resp.status_code != 200:
                return {"resolved": False, "error": resp.text}
            symbols = [s.get("symbol") for s in resp.json()]
            resolved = execution_symbol in symbols
            return {"resolved": resolved, "symbols_count": len(symbols)}

    async def place_order(
        self,
        account_id: str,
        execution_symbol: str,
        direction: str,
        volume: float,
        stop_loss: float,
        take_profit: Optional[float] = None,
        client_id: Optional[str] = None,
    ) -> dict[str, Any]:
        action_type = "ORDER_TYPE_BUY" if direction == "BUY" else "ORDER_TYPE_SELL"
        payload: dict[str, Any] = {
            "actionType": action_type,
            "symbol": execution_symbol,
            "volume": volume,
            "stopLoss": stop_loss,
            "clientId": client_id or f"td-{execution_symbol}",
        }
        if take_profit:
            payload["takeProfit"] = take_profit
        url = f"{self.BASE_URL}/users/current/accounts/{account_id}/trade"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=self.headers, json=payload)
            if resp.status_code in (200, 201):
                return {"status": "submitted", "data": resp.json()}
            return {"status": "error", "error": resp.text}

    async def get_positions(self, account_id: str) -> list[dict[str, Any]]:
        url = f"{self.BASE_URL}/users/current/accounts/{account_id}/positions"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=self.headers)
            if resp.status_code != 200:
                return []
            return resp.json()
