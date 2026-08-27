"""Backtest engine with mandatory cost modeling — spread + slippage."""

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
import pandas as pd


@dataclass
class BacktestConfig:
    spread_pips: float = 1.5
    slippage_pips: float = 0.5
    min_sample_size: int = 30


@dataclass
class BacktestResult:
    equity_curve: list[dict[str, Any]]
    trades: list[dict[str, Any]]
    max_drawdown: float
    profit_factor: Optional[float]
    sample_size: int
    confidence_label: str
    stats: dict[str, Any]


class BacktestEngine:
    def run(
        self,
        candles: list[dict[str, Any]],
        signals: list[dict[str, Any]],
        config: Optional[BacktestConfig] = None,
    ) -> BacktestResult:
        cfg = config or BacktestConfig()
        if len(candles) < 10:
            return BacktestResult([], [], 0.0, None, 0, "Insufficient data", {})

        df = pd.DataFrame(candles)
        trades: list[dict[str, Any]] = []
        equity = 10000.0
        peak = equity
        max_dd = 0.0
        wins = 0
        losses = 0
        gross_profit = 0.0
        gross_loss = 0.0
        curve = [{"bar": 0, "equity": equity}]

        cost_per_trade = (cfg.spread_pips + cfg.slippage_pips) * 0.0001 * equity * 0.01

        for i, sig in enumerate(signals):
            if i >= len(df) - 1:
                break
            entry = float(df.iloc[i]["close"])
            exit_price = float(df.iloc[min(i + 5, len(df) - 1)]["close"])
            direction = sig.get("direction", "BUY")
            pnl = (exit_price - entry) if direction == "BUY" else (entry - exit_price)
            pnl = pnl * 10000 - cost_per_trade
            equity += pnl
            peak = max(peak, equity)
            dd = (peak - equity) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
            if pnl > 0:
                wins += 1
                gross_profit += pnl
            else:
                losses += 1
                gross_loss += abs(pnl)
            trades.append({"entry": entry, "exit": exit_price, "pnl": pnl, "direction": direction})
            curve.append({"bar": i + 1, "equity": equity})

        sample = len(trades)
        pf = gross_profit / gross_loss if gross_loss > 0 else None
        label = "Insufficient data" if sample < cfg.min_sample_size else f"{wins / sample * 100:.1f}% win rate (n={sample})"

        return BacktestResult(
            equity_curve=curve,
            trades=trades,
            max_drawdown=max_dd,
            profit_factor=pf,
            sample_size=sample,
            confidence_label=label,
            stats={"wins": wins, "losses": losses, "final_equity": equity},
        )
