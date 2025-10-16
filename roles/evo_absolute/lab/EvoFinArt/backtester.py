"""Backtesting harness placeholder for EvoFinArt strategies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List

__all__ = ["BacktestResult", "FinArtBacktester"]


@dataclass
class BacktestResult:
    """Outcome snapshot from a simulated EvoFinArt run."""

    strategy: str
    started_at: datetime
    completed_at: datetime
    trades: List[Dict[str, float | str]]

    def to_dict(self) -> Dict[str, object]:
        return {
            "strategy": self.strategy,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "trades": self.trades,
        }


class FinArtBacktester:
    """Produces deterministic placeholder results for CI documentation."""

    def run(self, strategy: str) -> BacktestResult:
        now = datetime.now(timezone.utc)
        trades = [{"symbol": "SIM", "pnl": 0.0, "note": "placeholder"}]
        return BacktestResult(
            strategy=strategy,
            started_at=now,
            completed_at=now,
            trades=trades,
        )
