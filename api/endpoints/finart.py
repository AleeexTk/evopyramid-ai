"""FinArt channel endpoints for EvoPyramid API."""

from __future__ import annotations

from api.schemas.base import TradeSimulationRequest
from api.schemas.response import SimulationResult


def simulate_trade(request: TradeSimulationRequest) -> SimulationResult:
    """Return a deterministic placeholder simulation result."""

    expected_value = request.position_size * request.expected_edge
    return SimulationResult(
        strategy=request.strategy_name,
        horizon_minutes=request.horizon_minutes,
        expected_value=expected_value,
        metadata={
            "risk_limit": request.risk_limit,
            "bridge": "FinArt",
            "notes": "Placeholder simulation pending FinArt engine handshake.",
        },
    )
