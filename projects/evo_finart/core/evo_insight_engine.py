"""High-level orchestration for FinArt insights and Gemini reflections.

This module keeps the FinArt insight flow lightweight so it can run in
environments where the external Gemini service is unavailable. The additional
logging introduced here helps operators trace configuration issues and input
validation errors without relying on side-channel prints.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from projects.evo_finart.integrations.gemini_bridge import (
    GeminiConfig,
    GeminiFinArtBridge,
    GeminiReflection,
)


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "gemini_config.yaml"


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class InsightPacket:
    """Canonical representation of an EvoFinArt insight."""

    topic: str
    payload: Dict[str, Any]
    meta: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "topic": self.topic,
            "payload": self.payload,
        }
        if self.meta:
            data["meta"] = self.meta
        return data


class EvoInsightEngine:
    """Coordinates FinArt insights with Gemini reflections."""

    def __init__(
        self,
        *,
        config_path: Path | None = None,
        bridge: GeminiFinArtBridge | None = None,
    ) -> None:
        self._config_path = config_path or DEFAULT_CONFIG_PATH
        self._config = self._load_config(self._config_path)
        self._gemini_config = GeminiConfig.from_mapping(self._config)
        self._bridge = bridge or GeminiFinArtBridge(self._gemini_config)
        logger.debug(
            "EvoInsightEngine initialised", extra={"config_path": str(self._config_path)}
        )

    @property
    def bridge(self) -> GeminiFinArtBridge:
        return self._bridge

    @property
    def is_gemini_enabled(self) -> bool:
        return self._bridge.is_enabled

    def process(self, insight: InsightPacket | Dict[str, Any]) -> Dict[str, Any]:
        """Process a FinArt insight and optionally request a Gemini reflection.

        Parameters
        ----------
        insight:
            Either an :class:`InsightPacket` instance or a mapping with the
            ``topic`` and ``payload`` keys. When a mapping is supplied it will be
            coerced into an :class:`InsightPacket` to guarantee shape
            consistency.

        Returns
        -------
        dict
            A dictionary containing the normalised insight payload, the Gemini
            reflection (if produced) and metadata about the configuration used
            to process the request.
        """
        packet = insight if isinstance(insight, InsightPacket) else self._coerce_packet(insight)
        payload = packet.to_dict()

        reflection: GeminiReflection | None = None
        status = "ok"

        if self.is_gemini_enabled:
            reflection = self.bridge.reflect(payload)
        else:
            status = "gemini_disabled"
            logger.debug("Gemini disabled for EvoInsightEngine run", extra={"topic": packet.topic})

        result = {
            "insight": payload,
            "gemini": self._serialize_reflection(reflection),
            "status": status,
            "config": {
                "config_path": str(self._config_path),
                "gemini": self.bridge.to_dict(),
            },
        }
        logger.debug("EvoInsightEngine completed", extra={"status": status, "topic": packet.topic})
        return result

    def _load_config(self, path: Path) -> Dict[str, Any]:
        """Load Gemini configuration from YAML without external dependencies."""
        if not path.exists():
            logger.warning("Gemini config file missing; defaulting to disabled state", extra={"path": str(path)})
            return {"gemini": {"enabled": False}}
        return self._parse_simple_yaml(path.read_text(encoding="utf-8"))

    def _coerce_packet(self, payload: Dict[str, Any]) -> InsightPacket:
        """Normalise an incoming mapping into an :class:`InsightPacket`."""
        topic = payload.get("topic", "unspecified")
        body = payload.get("payload", {})
        meta = payload.get("meta")
        if not isinstance(body, dict):
            logger.error(
                "Insight payload must be a dictionary", extra={"topic": topic, "payload_type": type(body).__name__}
            )
            raise TypeError("Insight payload must be a dictionary.")
        return InsightPacket(topic=topic, payload=body, meta=meta)

    def _parse_simple_yaml(self, content: str) -> Dict[str, Any]:
        """Parse a subset of YAML used by the embedded Gemini configuration."""
        root: Dict[str, Any] = {}
        current_section: Optional[str] = None

        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if not raw_line.startswith(" ") and line.endswith(":"):
                section = line[:-1].strip()
                current_section = section
                root.setdefault(section, {})
                continue

            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            parsed_value: Any = self._coerce_scalar(value)

            if current_section and raw_line.startswith(" "):
                section_payload = root.setdefault(current_section, {})
                section_payload[key] = parsed_value
            else:
                root[key] = parsed_value

        return root

    def _coerce_scalar(self, value: str) -> Any:
        """Convert scalar string values found in configuration files."""
        if not value:
            return ""
        if value in {"true", "True"}:
            return True
        if value in {"false", "False"}:
            return False
        if value.startswith("\"") and value.endswith("\""):
            return value[1:-1]
        if value.startswith("'") and value.endswith("'"):
            return value[1:-1]
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value

    def _serialize_reflection(self, reflection: GeminiReflection | None) -> Optional[Dict[str, Any]]:
        """Convert a :class:`GeminiReflection` into a serialisable mapping."""
        if reflection is None:
            return None
        return {
            "text": reflection.text,
            "model": reflection.model,
            "context_scope": reflection.context_scope,
            "raw": reflection.raw,
        }


__all__ = [
    "EvoInsightEngine",
    "GeminiConfig",
    "GeminiFinArtBridge",
    "GeminiReflection",
    "InsightPacket",
]
