"""MetaApi REST connector — execution/account reads only."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

BASE_URL = "https://mt-client-api-v1.london.agiliumtrade.ai"
CONFIG_FILENAME = "metaapi.json"


@dataclass(frozen=True)
class MetaApiConfig:
    token: str = ""
    account_id: str = ""
    timeout: float = 30.0


def build_config(**overrides: Any) -> MetaApiConfig:
    token = str(overrides.get("token") or os.environ.get("METAAPI_TOKEN", "")).strip()
    account_id = str(overrides.get("account_id") or os.environ.get("METAAPI_ACCOUNT_ID", "")).strip()
    return MetaApiConfig(token=token, account_id=account_id)


def _headers(token: str) -> dict[str, str]:
    return {"auth-token": token, "Content-Type": "application/json"}


def check_status(**overrides: Any) -> dict[str, Any]:
    cfg = build_config(**overrides)
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


def get_account_snapshot(**overrides: Any) -> dict[str, Any]:
    status = check_status(**overrides)
    if not status.get("ok"):
        return {"status": "error", **status}
    return {
        "status": "ok",
        "account_id": status.get("account_id"),
        "cash": status.get("balance"),
        "equity": status.get("equity"),
        "buying_power": status.get("equity"),
    }


def get_positions(**overrides: Any) -> dict[str, Any]:
    cfg = build_config(**overrides)
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


def get_open_orders(**overrides: Any) -> dict[str, Any]:
    return {"status": "unsupported", "orders": []}


def get_quote(**_overrides: Any) -> dict[str, Any]:
    return {"status": "unsupported", "error": "MetaApi is execution-only; use OANDA for quotes"}


def get_historical_bars(**_overrides: Any) -> dict[str, Any]:
    return {"status": "unsupported", "error": "MetaApi is execution-only; use OANDA for candles"}
