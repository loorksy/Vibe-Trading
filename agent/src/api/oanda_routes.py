"""OANDA instrument catalog and pricing routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from src.providers.oanda.client import OandaClient

router = APIRouter(prefix="/api/oanda", tags=["oanda"])


def register_oanda_routes(app) -> None:
    app.include_router(router)


@router.get("/instruments")
def list_instruments(q: str = Query("", alias="q")) -> list[dict[str, Any]]:
    items = OandaClient().list_instruments()
    if q:
        needle = q.lower()
        items = [
            i for i in items
            if needle in i["display_symbol"].lower() or needle in i["canonical_id"].lower()
        ]
    return items


@router.get("/instruments/{canonical_id}/price")
def get_price(canonical_id: str) -> dict[str, Any]:
    client = OandaClient()
    return {"canonical_id": canonical_id, "price": client.get_price(canonical_id), "source": "oanda"}
