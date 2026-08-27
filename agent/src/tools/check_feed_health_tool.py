"""``check_feed_health`` — OANDA feed reliability for gates and UI banner."""

from __future__ import annotations

import json
import os
from typing import Any

from src.agent.tools import BaseTool
from src.providers.oanda.client import OandaClient


def check_feed_divergence(canonical_id: str) -> dict[str, Any]:
    client = OandaClient()
    price = client.get_price(canonical_id)
    oanda_mid = float(price["mid"]) if price else None
    twelve_raw = os.environ.get("TWELVE_DATA_MID", "").strip()
    twelve_mid = float(twelve_raw) if twelve_raw else None
    divergence_pct = None
    if oanda_mid and twelve_mid and oanda_mid > 0:
        divergence_pct = abs(oanda_mid - twelve_mid) / oanda_mid * 100
    threshold = float(os.environ.get("FEED_DIVERGENCE_THRESHOLD_PCT", "0.5"))
    reliable = oanda_mid is not None and (
        twelve_mid is None or divergence_pct is None or divergence_pct <= threshold
    )
    return {
        "canonical_id": canonical_id,
        "oanda_ok": price is not None,
        "oanda_mid": oanda_mid,
        "twelve_data_mid": twelve_mid,
        "divergence_pct": divergence_pct,
        "divergence_threshold_pct": threshold,
        "reliable": reliable,
        "source": "oanda",
    }


class CheckFeedHealthTool(BaseTool):
    """Report OANDA feed health and optional Twelve Data divergence."""

    name = "check_feed_health"
    description = (
        "Check whether the OANDA analysis feed is healthy for a symbol. "
        "Returns mid price, optional Twelve Data divergence, and a reliable flag "
        "used by validation gates and the UI feed banner."
    )
    parameters = {
        "type": "object",
        "properties": {
            "canonical_id": {
                "type": "string",
                "description": "OANDA canonical instrument id, e.g. EUR_USD.",
            },
        },
        "required": ["canonical_id"],
    }
    repeatable = True
    is_readonly = True
    deterministic = True

    def execute(self, **kwargs: Any) -> str:
        canonical_id = str(kwargs.get("canonical_id") or "EUR_USD").strip()
        return json.dumps(check_feed_divergence(canonical_id), ensure_ascii=False)
