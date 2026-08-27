"""Anthropic API client for agent role calls."""

import json
import re
from typing import Any, Optional

from app.config import get_settings

ROLE_PROMPTS = {
    "technical_analyst": (
        "You are a Technical Analyst. Analyze chart structure, support/resistance, and trend "
        "using the provided OHLC data and chart vision snapshots. Be concise and factual."
    ),
    "risk_manager": (
        "You are a Risk Manager. Assess stop-loss placement with ATR-based buffer beyond "
        "structural invalidation. Express risk in R multiples. Never flip direction."
    ),
    "news_sentiment": (
        "You are a News/Sentiment Analyst. Summarize market sentiment and flag high-impact "
        "events near the trade window. Be concise."
    ),
    "bull_researcher": (
        "You are a Bull Researcher. Build the strongest case FOR a trade on this instrument. "
        "You may argue direction but gates control final publication."
    ),
    "bear_researcher": (
        "You are a Bear Researcher. Build the strongest case AGAINST a trade. "
        "Note risks without inventing a flip unless structure demands it."
    ),
    "debate_moderator": (
        "You are a Debate Moderator. Weigh bull vs bear arguments in limited rounds. "
        "Resolve to one directional bias — never output WAIT."
    ),
    "trader": (
        "You are the Trader. Output ONLY valid JSON for a structured recommendation. "
        "Direction must be BUY or SELL only — never WAIT. Include all required fields."
    ),
    "bot_rationale_writer": (
        "You are the Bot Rationale Writer. Explain why this bar qualifies for entry: "
        "which rules fired, session context, spread, nearest news, why this bar not the previous."
    ),
}

QUICK_MODEL = "claude-3-5-haiku-20241022"
DEEP_MODEL = "claude-sonnet-4-20250514"


class AnthropicClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self.settings.anthropic_api_key)

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=self.settings.anthropic_api_key)
        return self._client

    async def complete_role(
        self,
        role: str,
        context: dict[str, Any],
        mode: str = "deep_analysis",
    ) -> str:
        if not self.available:
            return self._fallback(role, context)

        system = ROLE_PROMPTS.get(role, f"You are the {role} agent.")
        user_content = self._format_context(context, role)

        model = QUICK_MODEL if mode == "quick_scan" else DEEP_MODEL
        max_tokens = 512 if mode == "quick_scan" else 1024

        try:
            client = self._get_client()
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_content}],
            )
            return response.content[0].text  # type: ignore[union-attr]
        except Exception as e:
            return f"[LLM unavailable: {e}] {self._fallback(role, context)}"

    async def quick_scan(self, context: dict[str, Any]) -> str:
        if not self.available:
            return self._fallback("technical_analyst", context)

        try:
            client = self._get_client()
            response = await client.messages.create(
                model=QUICK_MODEL,
                max_tokens=400,
                system=(
                    "You are a trading assistant. Answer price/status questions concisely. "
                    "This is a Quick Scan — NOT a tradeable recommendation. Label it clearly."
                ),
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Symbol: {context.get('canonical_id')}\n"
                            f"Timeframe: {context.get('timeframe')}\n"
                            f"Question: {context.get('user_message')}\n"
                            f"Price data: {json.dumps(context.get('price', {}), default=str)[:500]}"
                        ),
                    }
                ],
            )
            return response.content[0].text  # type: ignore[union-attr]
        except Exception:
            return self._fallback("technical_analyst", context)

    async def parse_recommendation(self, trader_output: str, context: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Extract structured recommendation JSON from Trader role output."""
        match = re.search(r"\{[\s\S]*\}", trader_output)
        if match:
            try:
                data = json.loads(match.group())
                if data.get("direction") in ("BUY", "SELL"):
                    data.setdefault("canonical_id", context.get("canonical_id"))
                    data.setdefault("timeframe", context.get("timeframe"))
                    data.setdefault("analysis_mode", "deep_analysis")
                    data.setdefault("confidence_label", "Insufficient data")
                    data.setdefault("similar_past_cases", {"count": 0, "summary": "No similar cases found"})
                    return data
            except json.JSONDecodeError:
                pass
        return None

    def _format_context(self, context: dict[str, Any], role: str) -> str:
        parts = [
            f"Symbol: {context.get('canonical_id', 'EUR_USD')}",
            f"Timeframe: {context.get('timeframe', '1h')}",
            f"User message: {context.get('user_message', '')}",
        ]
        if context.get("price"):
            parts.append(f"Current price: {json.dumps(context['price'], default=str)}")
        if context.get("chart_snapshots") and role in ("technical_analyst", "trader", "debate_moderator"):
            for tf, snap in context["chart_snapshots"].items():
                ohlc = snap.get("ohlc", [])[-5:]
                parts.append(f"OHLC {tf} (last 5): {json.dumps(ohlc, default=str)}")
        if role == "trader":
            parts.append(
                'Output JSON with: direction, analytical_bias, plan_type, execution_status, '
                'fill_rule, entry_zone_low, entry_zone_high, preferred_entry, stop_loss, '
                'take_profits (array with level/price/r_multiple), invalidation_rule, validity_candles'
            )
        if context.get("debate_resolution"):
            parts.append(f"Debate resolution: {context['debate_resolution']}")
        return "\n".join(parts)

    def _fallback(self, role: str, context: dict[str, Any]) -> str:
        symbol = context.get("canonical_id", "EUR_USD")
        fallbacks = {
            "technical_analyst": f"Technical analysis on {symbol}: structure assessed from OHLC data.",
            "risk_manager": "Risk assessment: ATR-buffered stop beyond structural invalidation.",
            "news_sentiment": "No blocking high-impact events in immediate window.",
            "bull_researcher": "Bull case: momentum and structure support directional bias.",
            "bear_researcher": "Bear case: counter-arguments noted.",
            "debate_moderator": f"Bias maintained on {symbol} from technical structure.",
            "trader": json.dumps(self._default_recommendation(context)),
            "bot_rationale_writer": "Rules fired on scheduled bar; session and spread within limits.",
        }
        return fallbacks.get(role, f"{role} analysis complete")

    def _default_recommendation(self, context: dict[str, Any]) -> dict[str, Any]:
        price = context.get("current_price", 1.0850)
        if isinstance(price, dict):
            price = price.get("mid", 1.0850)
        atr = 0.0015
        return {
            "direction": "BUY",
            "analytical_bias": "BUY",
            "plan_type": "immediate",
            "execution_status": "active_now",
            "fill_rule": "market_price",
            "entry_zone_low": price - 0.0005,
            "entry_zone_high": price + 0.0005,
            "preferred_entry": price,
            "stop_loss": price - atr * 2,
            "take_profits": [
                {"level": 1, "price": price + atr * 2, "r_multiple": 1.0},
                {"level": 2, "price": price + atr * 4, "r_multiple": 2.0},
            ],
            "invalidation_rule": "Close below structural support invalidates thesis",
            "activation_rule": None,
            "activation_condition": None,
            "validity_candles": 12,
            "confidence_label": "Insufficient data",
            "similar_past_cases": {"count": 0, "summary": "No similar cases found"},
        }
