"""Claude Agent SDK orchestration — single spine, native Python tools only."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class AgentRole(str, Enum):
    TECHNICAL_ANALYST = "technical_analyst"
    RISK_MANAGER = "risk_manager"
    NEWS_SENTIMENT = "news_sentiment"
    BULL_RESEARCHER = "bull_researcher"
    BEAR_RESEARCHER = "bear_researcher"
    DEBATE_MODERATOR = "debate_moderator"
    TRADER = "trader"
    BOT_RATIONALE_WRITER = "bot_rationale_writer"


@dataclass
class AgentMessage:
    role: AgentRole
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisRequest:
    canonical_id: str
    timeframe: str
    mode: str  # quick_scan | deep_analysis
    user_message: str
    chart_snapshots: Optional[dict[str, Any]] = None


class AgentToolRegistry:
    """Native Python tools bound to Claude Agent SDK — READ/ANALYSIS only."""

    def __init__(self) -> None:
        self._tools: dict[str, Callable] = {}

    def register(self, name: str, fn: Callable, description: str) -> None:
        self._tools[name] = fn
        fn.__tool_description__ = description  # type: ignore[attr-defined]

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {"name": name, "description": getattr(fn, "__tool_description__", "")}
            for name, fn in self._tools.items()
        ]


class TradingAgentOrchestrator:
    """
    Multi-agent pipeline adapted from TradingAgents/crewAI role patterns.
    Claude Agent SDK is the ONLY runtime — no MCP, no nested products.
    """

    QUICK_ROLES = [AgentRole.TECHNICAL_ANALYST]
    DEEP_ROLES = [
        AgentRole.TECHNICAL_ANALYST,
        AgentRole.NEWS_SENTIMENT,
        AgentRole.BULL_RESEARCHER,
        AgentRole.BEAR_RESEARCHER,
        AgentRole.DEBATE_MODERATOR,
        AgentRole.RISK_MANAGER,
        AgentRole.TRADER,
    ]

    def __init__(self, tools: AgentToolRegistry) -> None:
        self.tools = tools
        self.transcript: list[AgentMessage] = []

    async def run_analysis(self, request: AnalysisRequest) -> dict[str, Any]:
        self.transcript = []
        roles = self.QUICK_ROLES if request.mode == "quick_scan" else self.DEEP_ROLES

        if request.mode == "deep_analysis" and not request.chart_snapshots:
            return {
                "published": False,
                "error": "Chart vision unavailable",
                "transcript": [],
            }

        context = await self._build_context(request)

        if request.mode == "deep_analysis":
            bull_case = await self._run_role(AgentRole.BULL_RESEARCHER, context)
            bear_case = await self._run_role(AgentRole.BEAR_RESEARCHER, context)
            synthesis = await self._run_debate(bull_case, bear_case, context)
            context["debate_resolution"] = synthesis

        for role in roles:
            if role in (AgentRole.BULL_RESEARCHER, AgentRole.BEAR_RESEARCHER, AgentRole.DEBATE_MODERATOR):
                continue
            await self._run_role(role, context)

        recommendation = await self._format_recommendation(request, context)
        return {
            "published": recommendation is not None,
            "recommendation": recommendation,
            "transcript": [
                {"role": m.role.value, "content": m.content, "metadata": m.metadata}
                for m in self.transcript
            ],
            "mode": request.mode,
        }

    async def write_bot_rationale(self, bot_context: dict[str, Any]) -> dict[str, Any]:
        msg = await self._run_role(AgentRole.BOT_RATIONALE_WRITER, bot_context)
        return {"rationale": msg.content, "metadata": msg.metadata}

    async def _build_context(self, request: AnalysisRequest) -> dict[str, Any]:
        return {
            "canonical_id": request.canonical_id,
            "timeframe": request.timeframe,
            "user_message": request.user_message,
            "chart_snapshots": request.chart_snapshots or {},
            "mode": request.mode,
        }

    async def _run_role(self, role: AgentRole, context: dict[str, Any]) -> AgentMessage:
        content = self._simulate_role_output(role, context)
        msg = AgentMessage(role=role, content=content)
        self.transcript.append(msg)
        return msg

    async def _run_debate(
        self, bull: AgentMessage, bear: AgentMessage, context: dict[str, Any]
    ) -> str:
        rounds = 2
        for i in range(rounds):
            self.transcript.append(
                AgentMessage(
                    role=AgentRole.DEBATE_MODERATOR,
                    content=f"Debate round {i + 1}: weighing bull vs bear arguments",
                    metadata={"round": i + 1},
                )
            )
        resolution = (
            f"Moderator resolves: directional bias maintained from technical structure "
            f"on {context['canonical_id']} {context['timeframe']}"
        )
        self.transcript.append(AgentMessage(role=AgentRole.DEBATE_MODERATOR, content=resolution))
        return resolution

    async def _format_recommendation(
        self, request: AnalysisRequest, context: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        if request.mode == "quick_scan":
            return None  # Quick scan never produces tradeable recommendations

        # Structured output from Trader role — direction never WAIT
        price = context.get("current_price", 1.0850)
        atr_buffer = 0.0015
        return {
            "canonical_id": request.canonical_id,
            "timeframe": request.timeframe,
            "direction": "BUY",
            "analytical_bias": "BUY",
            "plan_type": "immediate",
            "execution_status": "active_now",
            "fill_rule": "market_price",
            "entry_zone_low": price - 0.0005,
            "entry_zone_high": price + 0.0005,
            "preferred_entry": price,
            "stop_loss": price - atr_buffer * 2,
            "take_profits": [
                {"level": 1, "price": price + atr_buffer * 2, "r_multiple": 1.0},
                {"level": 2, "price": price + atr_buffer * 4, "r_multiple": 2.0},
            ],
            "invalidation_rule": "Close below structural support invalidates long thesis",
            "activation_rule": None,
            "activation_condition": None,
            "validity_candles": 12,
            "analysis_mode": request.mode,
            "confidence_label": "Insufficient data",
            "similar_past_cases": {"count": 0, "summary": "No similar cases found"},
        }

    def _simulate_role_output(self, role: AgentRole, context: dict[str, Any]) -> str:
        symbol = context.get("canonical_id", "EUR_USD")
        prompts = {
            AgentRole.TECHNICAL_ANALYST: f"Technical analysis on {symbol}: structure and levels assessed from chart vision and OHLC data.",
            AgentRole.RISK_MANAGER: "Risk assessment: stop placement uses ATR buffer beyond structural invalidation.",
            AgentRole.NEWS_SENTIMENT: "News/sentiment scan complete — no blocking high-impact events in immediate window.",
            AgentRole.BULL_RESEARCHER: "Bull case: momentum and structure support long bias.",
            AgentRole.BEAR_RESEARCHER: "Bear case: counter-arguments noted but do not flip analytical direction.",
            AgentRole.TRADER: "Final structured recommendation formatted per data model.",
            AgentRole.BOT_RATIONALE_WRITER: "Bot rationale: rules fired, session context, why this bar qualifies.",
        }
        return prompts.get(role, f"{role.value} analysis complete")
