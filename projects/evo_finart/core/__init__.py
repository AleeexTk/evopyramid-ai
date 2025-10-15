"""EvoFinArt core synchronization gateway for external integrators.

This module formalizes the canonical entry point used by :class:`EvoAbsolute`
to align a local Visual Studio laboratory with the living EvoPyramid
architecture.  It exposes utilities for retrieving synchronization manifests,
loading integration keys, and assembling a complete channel blueprint that can
be consumed by desktop automation scripts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

from apps.core.keys.key_loader import load_keys as _load_evo_keys

try:  # pragma: no cover - optional dependency in lightweight environments.
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_SYNC_MANIFEST = _REPO_ROOT / "EVO_SYNC_MANIFEST.yaml"
_DEFAULT_KEYS_PATH = _REPO_ROOT / "apps/core/keys/evo_keys.json"
_VISUAL_STUDIO_ENV = "visual_studio_windows"


class SyncManifestError(RuntimeError):
    """Raised when the synchronization manifest cannot be parsed."""


@dataclass(slots=True)
class DataExchangeProtocol:
    """Semantic contract for EvoPyramid data exchange channels."""

    name: str
    version: str
    transport: str
    payload_format: str
    heartbeat_interval: int
    handshake: Sequence[str]
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "transport": self.transport,
            "payload_format": self.payload_format,
            "heartbeat_interval": self.heartbeat_interval,
            "handshake": list(self.handshake),
            "notes": self.notes,
        }


@dataclass(slots=True)
class IntegrationKeyBundle:
    """Wrapper around EvoPyramid integration keys."""

    path: Path
    payload: Mapping[str, Any]

    def for_agent(self, agent_id: str) -> Mapping[str, Any]:
        data = self.payload.get(agent_id, {})
        if isinstance(data, Mapping):
            return data
        return {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "payload": dict(self.payload),
        }


@dataclass(slots=True)
class SyncManifest:
    """Holds the parsed synchronization manifest documents."""

    path: Path
    documents: Sequence[Mapping[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "documents": [dict(doc) for doc in self.documents],
        }

    @property
    def sync_policy(self) -> Mapping[str, Any]:
        return self.documents[0].get("sync_policy", {}) if self.documents else {}

    @property
    def directives(self) -> Sequence[Mapping[str, Any]]:
        return self.documents[0].get("directives", []) if self.documents else []

    @property
    def agents(self) -> Sequence[Mapping[str, Any]]:
        if len(self.documents) > 1:
            return self.documents[1].get("agents", [])
        return self.documents[0].get("agents", []) if self.documents else []

    def find_agent(self, agent_id: str) -> Optional[Mapping[str, Any]]:
        for agent in self.agents:
            if agent.get("id") == agent_id:
                return agent
        return None


@dataclass(slots=True)
class SyncChannelBlueprint:
    """Aggregated synchronization plan for EvoFinArt laboratories."""

    channel_id: str
    environment: str
    workspace: Path
    manifest: SyncManifest
    integration_keys: IntegrationKeyBundle
    protocol: DataExchangeProtocol
    instructions: Sequence[str]

    def to_payload(self) -> Dict[str, Any]:
        return {
            "channel_id": self.channel_id,
            "environment": self.environment,
            "workspace": str(self.workspace),
            "manifest": self.manifest.to_dict(),
            "integration_keys": self.integration_keys.to_dict(),
            "protocol": self.protocol.to_dict(),
            "instructions": list(self.instructions),
        }


def load_sync_manifest(path: Path | None = None) -> SyncManifest:
    """Load the Evo synchronization manifest as structured documents."""

    manifest_path = path or _DEFAULT_SYNC_MANIFEST
    if not manifest_path.exists():
        raise SyncManifestError(f"Sync manifest not found: {manifest_path}")

    if yaml is None:
        raise SyncManifestError(
            "PyYAML is required to parse the Evo sync manifest. Install it via "
            "`pip install pyyaml` inside the Visual Studio environment."
        )

    raw_content = manifest_path.read_text(encoding="utf-8")
    documents = [doc or {} for doc in yaml.safe_load_all(raw_content)]  # type: ignore[arg-type]
    if not documents:
        raise SyncManifestError(f"Manifest {manifest_path} does not contain any documents")
    return SyncManifest(path=manifest_path, documents=documents)


def load_integration_keys(path: Path | None = None) -> IntegrationKeyBundle:
    """Load EvoPyramid integration keys (sample-aware)."""

    keys_path = path or _DEFAULT_KEYS_PATH
    payload = _load_evo_keys(str(keys_path))
    return IntegrationKeyBundle(path=keys_path, payload=payload)


def default_visual_studio_protocol() -> DataExchangeProtocol:
    """Construct the canonical Visual Studio ↔ EvoPyramid protocol."""

    return DataExchangeProtocol(
        name="EvoSync.VisualStudio",
        version="1.0",
        transport="https+websocket",
        payload_format="json+kairos-envelope",
        heartbeat_interval=60,
        handshake=(
            "VS → local_sync_manager.py :: emit workspace heartbeat",
            "local_sync_manager.py → EvoRouter :: POST /api/router/sync",
            "EvoRouter → EvoMemory :: persist channel state",
            "Trinity Observer :: verify coherence and acknowledge",
        ),
        notes=(
            "Channel operates in monument→echo mode as specified by the global "
            "EVO_SYNC_MANIFEST. Visual Studio clients should batch file diffs "
            "before dispatching to EvoRouter to honor Kairos windows."
        ),
    )


def _visual_studio_instructions(workspace: Path, manifest: SyncManifest) -> Sequence[str]:
    agent = manifest.find_agent("evo_absolute") or {}
    repo_url = agent.get("repo", "https://github.com/AleeexTk/EvoFinArt")
    return (
        f"Clone or update EvoFinArt repository in Visual Studio: {repo_url}",
        "Place `apps/core/keys/evo_keys.json` (or copy the sample) in the lab to "
        "unlock scoped integrator credentials.",
        "Install dependencies: `pip install -r requirements.txt pyyaml`.",
        "Run `python -m apps.core.context.local_sync_manager` to emit local "
        "heartbeats before initiating workspace edits.",
        "Connect Visual Studio Task Runner to POST payloads to /api/router/sync "
        "using the Kairos envelope specified by the protocol.",
    )


def build_visual_studio_sync_blueprint(
    *,
    workspace: Path | str,
    channel_id: str = "EvoFinArt.VisualStudio",
    manifest_path: Path | None = None,
    keys_path: Path | None = None,
    protocol: DataExchangeProtocol | None = None,
) -> SyncChannelBlueprint:
    """Create a synchronization blueprint tailored for Visual Studio labs."""

    workspace_path = Path(workspace).expanduser().resolve()
    manifest = load_sync_manifest(manifest_path)
    keys = load_integration_keys(keys_path)
    channel_protocol = protocol or default_visual_studio_protocol()
    instructions = _visual_studio_instructions(workspace_path, manifest)

    return SyncChannelBlueprint(
        channel_id=channel_id,
        environment=_VISUAL_STUDIO_ENV,
        workspace=workspace_path,
        manifest=manifest,
        integration_keys=keys,
        protocol=channel_protocol,
        instructions=instructions,
    )


__all__ = [
    "DataExchangeProtocol",
    "IntegrationKeyBundle",
    "SyncChannelBlueprint",
    "SyncManifest",
    "SyncManifestError",
    "build_visual_studio_sync_blueprint",
    "default_visual_studio_protocol",
    "load_integration_keys",
    "load_sync_manifest",
]
