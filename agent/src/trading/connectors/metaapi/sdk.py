"""MetaApi REST connector — execution and account reads only."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import httpx

from src.config.paths import get_runtime_root
from src.trading.connectors.metaapi.symbols import canonical_to_execution_symbol

BASE_URL = "https://mt-client-api-v1.london.agiliumtrade.ai"
CONFIG_FILENAME = "metaapi.json"
_CONTRACT_UNITS = 100_000.0


@dataclass(frozen=True)
class MetaApiConfig:
    token: str = ""
    account_id: str = ""
    timeout: float = 30.0
    profile: str = "live"


def _config_path() -> Path:
    return get_runtime_root() / CONFIG_FILENAME


def _load_file_config() -> dict[str, Any]:
    path = _config_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def build_config(
    profile_config: Mapping[str, Any] | None = None,
    overrides: Mapping[str, Any] | None = None,
) -> MetaApiConfig:
    merged: dict[str, Any] = {}
    merged.update(_load_file_config())
    if profile_config:
        merged.update(profile_config)
    if overrides:
        merged.update(overrides)
    token = str(merged.get("token") or os.environ.get("METAAPI_TOKEN", "")).strip()
    account_id = str(merged.get("account_id") or os.environ.get("METAAPI_ACCOUNT_ID", "")).strip()
    profile = str(merged.get("profile") or "live")
    timeout = float(merged.get("timeout") or 30.0)
    return MetaApiConfig(token=token, account_id=account_id, timeout=timeout, profile=profile)


def _headers(token: str) -> dict[str, str]:
    return {"auth-token": token, "Content-Type": "application/json"}


def check_status(config: MetaApiConfig | None = None, **overrides: Any) -> dict[str, Any]:
    cfg = config or build_config(overrides=overrides)
    if not cfg.token:
        return {"ok": False, "error": "METAAPI_TOKEN not configured"}
    if not cfg.account_id:
        return {"ok": False, "error": "METAAPI_ACCOUNT_ID not configured"}
    url = f"{BASE_URL}/users/current/accounts/{cfg.account_id}/account-information"
    try:
        with httpx.Client(timeout=cfg.timeout) as client:
            resp = client.get(url, headers=_headers(cfg.token))
        if resp.status_code != 200:
            return {"ok": False, "error": resp.text, "status_code": resp.status_code}
        data = resp.json()
        return {
            "ok": True,
            "account_id": cfg.account_id,
            "balance": data.get("balance"),
            "equity": data.get("equity"),
            "margin": data.get("margin"),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def get_account_snapshot(config: MetaApiConfig | None = None, **overrides: Any) -> dict[str, Any]:
    status = check_status(config, **overrides)
    if not status.get("ok"):
        return {"status": "error", **status}
    return {
        "status": "ok",
        "account_id": status.get("account_id"),
        "cash": status.get("balance"),
        "equity": status.get("equity"),
        "buying_power": status.get("equity"),
    }


def get_positions(config: MetaApiConfig | None = None, **overrides: Any) -> dict[str, Any]:
    cfg = config or build_config(overrides=overrides)
    if not cfg.token or not cfg.account_id:
        return {"status": "error", "error": "MetaApi credentials not configured"}
    url = f"{BASE_URL}/users/current/accounts/{cfg.account_id}/positions"
    try:
        with httpx.Client(timeout=cfg.timeout) as client:
            resp = client.get(url, headers=_headers(cfg.token))
        if resp.status_code != 200:
            return {"status": "error", "error": resp.text}
        return {"status": "ok", "positions": resp.json()}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc)}


def get_open_orders(config: MetaApiConfig | None = None, **_overrides: Any) -> dict[str, Any]:
    del config
    return {"status": "unsupported", "orders": []}


def get_quote(config: MetaApiConfig | None = None, **_overrides: Any) -> dict[str, Any]:
    del config
    return {"status": "unsupported", "error": "MetaApi is execution-only; use OANDA for quotes"}


def get_historical_bars(config: MetaApiConfig | None = None, **_overrides: Any) -> dict[str, Any]:
    del config
    return {"status": "unsupported", "error": "MetaApi is execution-only; use OANDA for candles"}


def quantity_notional_usd(
    config: MetaApiConfig | None,
    symbol: str,
    quantity: float,
) -> float | None:
    """Approximate USD notional for FX lots (100k units per lot)."""
    if quantity <= 0:
        return None
    try:
        from src.providers.oanda.client import OandaClient

        display = canonical_to_execution_symbol(symbol)
        price = OandaClient().get_price(display) or OandaClient().get_price(symbol)
        mid = float((price or {}).get("mid") or 0)
        if mid <= 0:
            return None
        return abs(quantity) * _CONTRACT_UNITS * mid
    except Exception:  # noqa: BLE001
        return None


def place_order(
    config: MetaApiConfig,
    *,
    symbol: str,
    side: str,
    quantity: float | None = None,
    notional: float | None = None,
    order_type: str = "market",
    limit_price: float | None = None,
    stop_loss: float | None = None,
    take_profit: float | None = None,
    execution_symbol: str | None = None,
    client_id: str | None = None,
    **_kwargs: Any,
) -> dict[str, Any]:
    del order_type, limit_price, notional
    if not config.token or not config.account_id:
        return {"status": "error", "error": "MetaApi credentials not configured"}
    if quantity is None or quantity <= 0:
        return {"status": "error", "error": "quantity (lots) is required for MetaApi orders"}
    direction = str(side or "").strip().upper()
    if direction not in {"BUY", "SELL"}:
        return {"status": "error", "error": "side must be BUY or SELL"}
    exec_symbol = execution_symbol or canonical_to_execution_symbol(symbol)
    action_type = "ORDER_TYPE_BUY" if direction == "BUY" else "ORDER_TYPE_SELL"
    payload: dict[str, Any] = {
        "actionType": action_type,
        "symbol": exec_symbol,
        "volume": float(quantity),
        "clientId": client_id or f"vibe-{exec_symbol}",
    }
    if stop_loss is not None:
        payload["stopLoss"] = float(stop_loss)
    if take_profit is not None:
        payload["takeProfit"] = float(take_profit)
    url = f"{BASE_URL}/users/current/accounts/{config.account_id}/trade"
    try:
        with httpx.Client(timeout=config.timeout) as client:
            resp = client.post(url, headers=_headers(config.token), json=payload)
        if resp.status_code in (200, 201):
            return {"status": "ok", "broker": "metaapi", "data": resp.json(), "symbol": exec_symbol}
        return {"status": "error", "error": resp.text, "status_code": resp.status_code}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc)}


def cancel_order(
    config: MetaApiConfig,
    order_id: str,
    *,
    symbol: str | None = None,
    **_kwargs: Any,
) -> dict[str, Any]:
    del symbol
    if not config.token or not config.account_id:
        return {"status": "error", "error": "MetaApi credentials not configured"}
    url = f"{BASE_URL}/users/current/accounts/{config.account_id}/trade"
    payload = {"actionType": "POSITION_CLOSE_ID", "positionId": order_id}
    try:
        with httpx.Client(timeout=config.timeout) as client:
            resp = client.post(url, headers=_headers(config.token), json=payload)
        if resp.status_code in (200, 201):
            return {"status": "ok", "data": resp.json()}
        return {"status": "error", "error": resp.text}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc)}
