"""Persisted trade recommendations (gated, surface-executable)."""

from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from contextlib import suppress
from pathlib import Path
from typing import Any, Mapping

from src.config.paths import get_runtime_root

_ID_RE = re.compile(r"^tr_[0-9a-f]{32}$")
_TTL_MS = 24 * 60 * 60 * 1000
_LOCK = threading.Lock()


class RecommendationError(ValueError):
    pass


def _path(recommendation_id: str) -> Path:
    if not _ID_RE.fullmatch(recommendation_id):
        raise RecommendationError("invalid trade recommendation id")
    return get_runtime_root() / "trade_recommendations" / f"{recommendation_id}.json"


def _write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        try:
            with os.fdopen(fd, "wb") as handle:
                fd = -1
                handle.write(
                    (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode()
                )
                handle.flush()
                os.fsync(handle.fileno())
        finally:
            if fd >= 0:
                os.close(fd)
        os.replace(tmp, path)
    except BaseException:
        with suppress(OSError):
            os.unlink(tmp)
        raise
    os.chmod(path, 0o600)


def public_recommendation(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "type": "trade.recommendation",
        "recommendation_id": payload["recommendation_id"],
        "session_id": payload.get("session_id"),
        "canonical_id": payload["canonical_id"],
        "display_symbol": payload.get("display_symbol", payload["canonical_id"]),
        "timeframe": payload.get("timeframe", "H1"),
        "direction": payload["direction"],
        "analytical_bias": payload.get("analytical_bias", ""),
        "plan_type": payload.get("plan_type", "trade"),
        "execution_status": payload.get("execution_status", "not_ready"),
        "analysis_mode": payload.get("analysis_mode", "deep"),
        "entry_zone": payload.get("entry_zone"),
        "preferred_entry": payload.get("preferred_entry"),
        "stop_loss": payload.get("stop_loss"),
        "take_profits": payload.get("take_profits") or [],
        "gate_results": payload.get("gate_results") or [],
        "publishable": bool(payload.get("publishable")),
        "created_at": payload.get("created_at"),
        "expires_at": payload.get("expires_at"),
        "status": payload.get("status", "pending"),
        "executed_at": payload.get("executed_at"),
    }


def save_recommendation(payload: Mapping[str, Any]) -> dict[str, Any]:
    recommendation_id = str(payload.get("recommendation_id") or f"tr_{uuid.uuid4().hex}")
    if not _ID_RE.fullmatch(recommendation_id):
        raise RecommendationError("invalid recommendation id")
    now = int(time.time() * 1000)
    record = {
        **dict(payload),
        "recommendation_id": recommendation_id,
        "type": "trade.recommendation",
        "created_at": payload.get("created_at", now),
        "expires_at": payload.get("expires_at", now + _TTL_MS),
        "status": payload.get("status", "pending"),
    }
    with _LOCK:
        _write(_path(recommendation_id), record)
    return public_recommendation(record)


def load_recommendation(recommendation_id: str) -> dict[str, Any]:
    path = _path(recommendation_id)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RecommendationError(f"recommendation {recommendation_id!r} is unknown") from exc
    if not isinstance(payload, dict):
        raise RecommendationError("recommendation record is malformed")
    return payload


def mark_executed(recommendation_id: str, execution: Mapping[str, Any]) -> dict[str, Any]:
    with _LOCK:
        record = load_recommendation(recommendation_id)
        record["status"] = "executed"
        record["executed_at"] = int(time.time() * 1000)
        record["execution"] = dict(execution)
        _write(_path(recommendation_id), record)
    return public_recommendation(record)
