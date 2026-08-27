"""Chart vision — capture candlestick images + OHLC for deep analysis."""

import base64
import io
from typing import Any, Optional

from app.services.market_data import OandaService

TIMEFRAME_MAP = {"15m": "M15", "1h": "H1", "4h": "H4", "1d": "D", "5m": "M5", "30m": "M30"}


class ChartVisionService:
    def __init__(self) -> None:
        self.oanda = OandaService()

    async def capture(
        self,
        canonical_id: str,
        active_timeframe: str = "1h",
        timeframes: Optional[list[str]] = None,
    ) -> Optional[dict[str, Any]]:
        tfs = timeframes or ["15m", "1h", "4h"]
        if active_timeframe not in tfs:
            tfs.append(active_timeframe)

        snapshots: dict[str, Any] = {}
        for tf in tfs:
            gran = TIMEFRAME_MAP.get(tf, "H1")
            candles = await self.oanda.get_candles(canonical_id, gran, 100)
            if not candles:
                continue
            image_b64 = self._render_chart(candles, canonical_id, tf)
            snapshots[tf] = {
                "ohlc": candles[-30:],
                "image_b64": image_b64,
                "image_ref": f"snapshot:{canonical_id}:{tf}",
                "candle_count": len(candles),
            }

        return snapshots if snapshots else None

    def _render_chart(
        self,
        candles: list[dict[str, Any]],
        symbol: str,
        timeframe: str,
    ) -> Optional[str]:
        if not candles:
            return None
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from datetime import datetime

            fig, ax = plt.subplots(figsize=(8, 4), facecolor="#0f1419")
            ax.set_facecolor("#0f1419")

            times = []
            for c in candles[-60:]:
                t = c.get("time", "")
                try:
                    times.append(datetime.fromisoformat(t.replace("Z", "+00:00")))
                except ValueError:
                    times.append(datetime.now())

            opens = [c["open"] for c in candles[-60:]]
            highs = [c["high"] for c in candles[-60:]]
            lows = [c["low"] for c in candles[-60:]]
            closes = [c["close"] for c in candles[-60:]]

            for i in range(len(times)):
                color = "#22c55e" if closes[i] >= opens[i] else "#ef4444"
                ax.plot([i, i], [lows[i], highs[i]], color=color, linewidth=0.8)
                body_bottom = min(opens[i], closes[i])
                body_height = max(abs(closes[i] - opens[i]), (max(highs) - min(lows)) * 0.001)
                ax.bar(i, body_height, bottom=body_bottom, width=0.6, color=color)

            ax.set_title(f"{symbol} {timeframe}", color="#e5e7eb", fontsize=10)
            ax.tick_params(colors="#6b7280", labelsize=7)
            for spine in ax.spines.values():
                spine.set_color("#374151")
            ax.grid(True, alpha=0.15, color="#374151")

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="#0f1419")
            plt.close(fig)
            buf.seek(0)
            return base64.b64encode(buf.read()).decode("utf-8")
        except Exception:
            return None
