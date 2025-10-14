"""High-level orchestration for FinArt insights and Gemini reflections."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from projects.evo_finart.integrations.gemini_bridge import (
    GeminiConfig,
    GeminiFinArtBridge,
    GeminiReflection,
)


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "gemini_config.yaml"


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

    @property
    def bridge(self) -> GeminiFinArtBridge:
        return self._bridge

    @property
    def is_gemini_enabled(self) -> bool:
        return self._bridge.is_enabled

    def process(self, insight: InsightPacket | Dict[str, Any]) -> Dict[str, Any]:
        packet = insight if isinstance(insight, InsightPacket) else self._coerce_packet(insight)
        payload = packet.to_dict()

        reflection: GeminiReflection | None = None
        status = "ok"

        if self.is_gemini_enabled:
            reflection = self.bridge.reflect(payload)
        else:
            status = "gemini_disabled"

        return {
            "insight": payload,
            "gemini": self._serialize_reflection(reflection),
            "status": status,
            "config": {
                "config_path": str(self._config_path),
                "gemini": self._public_bridge_config(),
            },
        }

    def _public_bridge_config(self) -> Dict[str, Any]:
        """Return sanitized bridge configuration safe for public exposure."""

        config = dict(self.bridge.to_dict())
        # Redact secrets that may have been provided directly in the config file.
        config.pop("api_key", None)
        return config

    def _load_config(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {"gemini": {"enabled": False}}
        return self._parse_simple_yaml(path.read_text(encoding="utf-8"))

    def _coerce_packet(self, payload: Dict[str, Any]) -> InsightPacket:
        topic = payload.get("topic", "unspecified")
        body = payload.get("payload", {})
        meta = payload.get("meta")
        if not isinstance(body, dict):
            raise TypeError("Insight payload must be a dictionary.")
        return InsightPacket(topic=topic, payload=body, meta=meta)

    def _parse_simple_yaml(self, content: str) -> Dict[str, Any]:
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
