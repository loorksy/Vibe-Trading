"""Claude Agent SDK orchestration — single spine, native Python tools only."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Callable, Optional

from app.agents.llm import AnthropicClient


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
    price: Optional[dict[str, Any]] = None


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
        self.llm = AnthropicClient()

    async def run_analysis(self, request: AnalysisRequest) -> dict[str, Any]:
        self.transcript = []

        if request.mode == "quick_scan":
            context = await self._build_context(request)
            content = await self.llm.quick_scan(context)
            self.transcript.append(AgentMessage(role=AgentRole.TECHNICAL_ANALYST, content=content))
            return {
                "published": False,
                "quick_scan_response": content,
                "transcript": self._serialize_transcript(),
                "mode": request.mode,
            }

        if request.mode == "deep_analysis" and not request.chart_snapshots:
            return {
                "published": False,
                "error": "Chart vision unavailable",
                "transcript": [],
            }

        context = await self._build_context(request)

        bull_case = await self._run_role(AgentRole.BULL_RESEARCHER, context, request.mode)
        bear_case = await self._run_role(AgentRole.BEAR_RESEARCHER, context, request.mode)
        synthesis = await self._run_debate(bull_case, bear_case, context)
        context["debate_resolution"] = synthesis

        for role in self.DEEP_ROLES:
            if role in (AgentRole.BULL_RESEARCHER, AgentRole.BEAR_RESEARCHER, AgentRole.DEBATE_MODERATOR):
                continue
            await self._run_role(role, context, request.mode)

        recommendation = await self._format_recommendation(request, context)
        return {
            "published": recommendation is not None,
            "recommendation": recommendation,
            "transcript": self._serialize_transcript(),
            "mode": request.mode,
        }

    async def run_analysis_stream(self, request: AnalysisRequest) -> AsyncIterator[dict[str, Any]]:
        """SSE-friendly generator yielding role progress events."""
        self.transcript = []

        if request.mode == "quick_scan":
            context = await self._build_context(request)
            yield {"event": "role_start", "role": "technical_analyst"}
            content = await self.llm.quick_scan(context)
            self.transcript.append(AgentMessage(role=AgentRole.TECHNICAL_ANALYST, content=content))
            yield {"event": "role_complete", "role": "technical_analyst", "content": content}
            yield {"event": "complete", "published": False, "quick_scan_response": content}
            return

        if request.mode == "deep_analysis" and not request.chart_snapshots:
            yield {"event": "error", "message": "Chart vision unavailable"}
            return

        context = await self._build_context(request)
        all_roles = [
            AgentRole.BULL_RESEARCHER,
            AgentRole.BEAR_RESEARCHER,
            AgentRole.TECHNICAL_ANALYST,
            AgentRole.NEWS_SENTIMENT,
            AgentRole.RISK_MANAGER,
            AgentRole.TRADER,
        ]

        for role in all_roles:
            yield {"event": "role_start", "role": role.value}
            if role == AgentRole.BULL_RESEARCHER:
                msg = await self._run_role(role, context, request.mode)
                bear = await self._run_role(AgentRole.BEAR_RESEARCHER, context, request.mode)
                synthesis = await self._run_debate(msg, bear, context)
                context["debate_resolution"] = synthesis
                yield {"event": "role_complete", "role": role.value, "content": msg.content}
                yield {"event": "role_complete", "role": "bear_researcher", "content": bear.content}
                yield {"event": "role_complete", "role": "debate_moderator", "content": synthesis}
                continue
            if role == AgentRole.BEAR_RESEARCHER:
                continue
            msg = await self._run_role(role, context, request.mode)
            yield {"event": "role_complete", "role": role.value, "content": msg.content}

        recommendation = await self._format_recommendation(request, context)
        yield {
            "event": "complete",
            "published": recommendation is not None,
            "recommendation": recommendation,
            "transcript": self._serialize_transcript(),
        }

    async def write_bot_rationale(self, bot_context: dict[str, Any]) -> dict[str, Any]:
        msg = await self._run_role(AgentRole.BOT_RATIONALE_WRITER, bot_context, "deep_analysis")
        return {"rationale": msg.content, "metadata": msg.metadata}

    async def _build_context(self, request: AnalysisRequest) -> dict[str, Any]:
        ctx: dict[str, Any] = {
            "canonical_id": request.canonical_id,
            "timeframe": request.timeframe,
            "user_message": request.user_message,
            "chart_snapshots": request.chart_snapshots or {},
            "mode": request.mode,
        }
        if request.price:
            ctx["price"] = request.price
            ctx["current_price"] = request.price.get("mid")
        return ctx

    async def _run_role(self, role: AgentRole, context: dict[str, Any], mode: str) -> AgentMessage:
        content = await self.llm.complete_role(role.value, context, mode)
        msg = AgentMessage(role=role, content=content)
        self.transcript.append(msg)
        return msg

    async def _run_debate(
        self, bull: AgentMessage, bear: AgentMessage, context: dict[str, Any]
    ) -> str:
        for i in range(2):
            round_content = await self.llm.complete_role(
                "debate_moderator",
                {**context, "bull_case": bull.content, "bear_case": bear.content, "round": i + 1},
                "deep_analysis",
            )
            self.transcript.append(
                AgentMessage(
                    role=AgentRole.DEBATE_MODERATOR,
                    content=round_content,
                    metadata={"round": i + 1},
                )
            )
        resolution = await self.llm.complete_role(
            "debate_moderator",
            {**context, "bull_case": bull.content, "bear_case": bear.content, "final": True},
            "deep_analysis",
        )
        self.transcript.append(AgentMessage(role=AgentRole.DEBATE_MODERATOR, content=resolution))
        return resolution

    async def _format_recommendation(
        self, request: AnalysisRequest, context: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        trader_msgs = [m for m in self.transcript if m.role == AgentRole.TRADER]
        if not trader_msgs:
            return None

        parsed = await self.llm.parse_recommendation(trader_msgs[-1].content, context)
        if parsed:
            parsed["canonical_id"] = request.canonical_id
            parsed["timeframe"] = request.timeframe
            parsed["analysis_mode"] = request.mode
            return parsed

        default = self.llm._default_recommendation(context)
        default["canonical_id"] = request.canonical_id
        default["timeframe"] = request.timeframe
        default["analysis_mode"] = request.mode
        return default

    def _serialize_transcript(self) -> list[dict[str, Any]]:
        return [
            {"role": m.role.value, "content": m.content, "metadata": m.metadata}
            for m in self.transcript
        ]
