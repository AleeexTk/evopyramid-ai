"""Gemini bridge dedicated to the EvoFinArt surface."""

from __future__ import annotations

import importlib
import json
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass(slots=True)
class GeminiConfig:
    """Configuration container for the Gemini bridge."""

    model: str = "gemini-1.5-pro"
    api_key_env: str = "GEMINI_API_KEY"
    enabled: bool = True
    context_scope: Optional[str] = None
    output_mode: str = "text"
    api_key: Optional[str] = None

    @classmethod
    def from_mapping(cls, payload: Dict[str, Any]) -> "GeminiConfig":
        gemini_payload = payload.get("gemini", payload)
        return cls(
            model=gemini_payload.get("model", cls.model),
            api_key_env=gemini_payload.get("api_key_env", cls.api_key_env),
            enabled=bool(gemini_payload.get("enabled", cls.enabled)),
            context_scope=gemini_payload.get("context_scope"),
            output_mode=gemini_payload.get("output_mode", cls.output_mode),
            api_key=gemini_payload.get("api_key"),
        )


@dataclass(slots=True)
class GeminiReflection:
    """Normalized reflection returned from Gemini."""

    text: str
    model: str
    context_scope: Optional[str]
    raw: Dict[str, Any]


class GeminiFinArtBridge:
    """Wrapper responsible for coordinating Gemini calls for EvoFinArt."""

    def __init__(self, config: GeminiConfig):
        self.config = config
        self._client: Any | None = None

    @classmethod
    def from_config(cls, payload: Dict[str, Any]) -> "GeminiFinArtBridge":
        return cls(GeminiConfig.from_mapping(payload))

    @property
    def is_enabled(self) -> bool:
        return self.config.enabled

    def reflect(self, insight: Dict[str, Any]) -> GeminiReflection:
        """Send an insight payload to Gemini and normalize the response."""

        if not self.is_enabled:
            return GeminiReflection(
                text="",
                model=self.config.model,
                context_scope=self.config.context_scope,
                raw={
                    "status": "disabled",
                    "insight": insight,
                },
            )

        client = self._ensure_client()
        prompt = self._build_prompt(insight)
        response = client.generate_content(prompt)
        text = self._extract_text(response)
        raw_response = self._serialize_response(response)

        return GeminiReflection(
            text=text,
            model=self.config.model,
            context_scope=self.config.context_scope,
            raw={
                "output_mode": self.config.output_mode,
                "response": raw_response,
                "prompt": prompt,
            },
        )

    def _ensure_client(self):
        if self._client is not None:
            return self._client

        module = importlib.import_module("google.generativeai")
        api_key = self.config.api_key or os.getenv(self.config.api_key_env, "")
        if not api_key:
            raise RuntimeError(
                "Gemini API key is missing. Set the configured environment variable "
                f"{self.config.api_key_env}."
            )

        module.configure(api_key=api_key)
        self._client = module.GenerativeModel(self.config.model)
        return self._client

    def _build_prompt(self, insight: Dict[str, Any]) -> str:
        body = json.dumps(insight, indent=2, ensure_ascii=False)
        context = self.config.context_scope or "FinArt-Insight"
        mode = self.config.output_mode
        return (
            "You are Gemini-FinArt, the coherence companion for EvoFinArt insights.\n"
            "Respond with clarity, empathy, and tactical awareness.\n"
            f"Context-Scope: {context}\n"
            f"Output-Mode: {mode}\n"
            "--- Insight Payload ---\n"
            f"{body}\n"
        )

    def _extract_text(self, response: Any) -> str:
        text = getattr(response, "text", None)
        if text:
            return text

        candidates = getattr(response, "candidates", None)
        if candidates:
            for candidate in candidates:
                content = getattr(candidate, "content", None)
                if content:
                    parts = getattr(content, "parts", None) or []
                    for part in parts:
                        value = getattr(part, "text", None)
                        if value:
                            return value
        return ""

    def _serialize_response(self, response: Any) -> Dict[str, Any]:
        if hasattr(response, "to_dict"):
            return response.to_dict()  # type: ignore[return-value]
        if isinstance(response, dict):
            return response
        return {"repr": repr(response)}

    def to_dict(self, *, include_sensitive: bool = False) -> Dict[str, Any]:
        data = asdict(self.config)
        if not include_sensitive:
            data.pop("api_key", None)
        return data
