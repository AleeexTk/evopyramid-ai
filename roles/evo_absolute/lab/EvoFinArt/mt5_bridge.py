"""MetaTrader 5 bridge placeholder for EvoFinArt."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional

__all__ = ["BridgeStatus", "MT5Bridge"]


@dataclass
class BridgeStatus:
    """Represents the state of the EvoFinArt ↔ MT5 link."""

    connected: bool
    account: Optional[str]
    last_sync: datetime

    def to_dict(self) -> Dict[str, str | bool | None]:
        return {
            "connected": self.connected,
            "account": self.account,
            "last_sync": self.last_sync.isoformat(),
        }


class MT5Bridge:
    """Lightweight shim that records bridge intent without performing trades."""

    def connect(self, account: Optional[str] = None) -> BridgeStatus:
        return BridgeStatus(connected=True, account=account, last_sync=datetime.now(timezone.utc))

    def disconnect(self) -> BridgeStatus:
        return BridgeStatus(connected=False, account=None, last_sync=datetime.now(timezone.utc))
