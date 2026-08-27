"""MetaApi symbol helpers — execution mapping and mandate classification."""

from __future__ import annotations

from src.live.mandate.model import AssetClass, InstrumentType
from src.providers.oanda.client import _canonical_to_oanda, _oanda_to_display


def canonical_to_execution_symbol(canonical_id: str, alias: str | None = None) -> str:
    if alias:
        return alias.strip()
    return _oanda_to_display(_canonical_to_oanda(canonical_id))


def classify_metaapi_symbol(symbol: str) -> tuple[InstrumentType, AssetClass | None]:
    token = (symbol or "").strip().upper()
    if len(token) == 6 and token.isalpha():
        return InstrumentType.FOREX, AssetClass.FOREX
    if token.startswith(("XAU", "XAG")):
        return InstrumentType.CFD, None
    return InstrumentType.CFD, None
