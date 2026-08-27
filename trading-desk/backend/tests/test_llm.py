import pytest
from app.agents.llm import AnthropicClient


def test_fallback_when_no_api_key():
    client = AnthropicClient()
    result = client._fallback("technical_analyst", {"canonical_id": "EUR_USD"})
    assert "EUR_USD" in result


def test_default_recommendation_never_wait():
    client = AnthropicClient()
    rec = client._default_recommendation({"current_price": 1.0850})
    assert rec["direction"] in ("BUY", "SELL")
    assert rec["direction"] != "WAIT"
    assert len(rec["take_profits"]) >= 2


@pytest.mark.asyncio
async def test_quick_scan_fallback():
    client = AnthropicClient()
    result = await client.quick_scan({
        "canonical_id": "EUR_USD",
        "timeframe": "1h",
        "user_message": "What is price doing?",
    })
    assert len(result) > 0


@pytest.mark.asyncio
async def test_parse_recommendation_from_json():
    client = AnthropicClient()
    output = '{"direction": "SELL", "analytical_bias": "SELL", "plan_type": "immediate", "execution_status": "active_now", "fill_rule": "market_price", "entry_zone_low": 1.08, "entry_zone_high": 1.09, "preferred_entry": 1.085, "stop_loss": 1.095, "take_profits": [{"level": 1, "price": 1.07}], "invalidation_rule": "test", "validity_candles": 10}'
    parsed = await client.parse_recommendation(output, {"canonical_id": "EUR_USD", "timeframe": "1h"})
    assert parsed is not None
    assert parsed["direction"] == "SELL"
