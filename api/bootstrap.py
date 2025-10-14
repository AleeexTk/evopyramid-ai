"""Manifest bootstrap utilities for the EvoPyramid API."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping

import yaml

from .router import EvoRouter, RouteSpec

__all__ = ["ManifestError", "load_manifest", "bootstrap_router_from_manifest"]


class ManifestError(RuntimeError):
    """Raised when the EvoPyramid API manifest cannot be processed."""


def load_manifest(path: str | Path | None = None) -> MutableMapping[str, Any]:
    """Load the EvoPyramid API manifest from disk.

    Args:
        path: Optional override path. Defaults to ``api/manifest.yaml`` next to
            this module.

    Returns:
        The parsed manifest mapping.

    Raises:
        ManifestError: If the manifest file is missing or does not evaluate to a
            mapping structure.
    """

    manifest_path = Path(path) if path is not None else Path(__file__).with_name("manifest.yaml")
    if not manifest_path.exists():
        raise ManifestError(f"Manifest file not found: {manifest_path}")

    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, MutableMapping):
        raise ManifestError("Manifest root must be a mapping structure")
    return data


def bootstrap_router_from_manifest(
    router: EvoRouter,
    *,
    manifest: Mapping[str, Any] | None = None,
    manifest_path: str | Path | None = None,
) -> EvoRouter:
    """Populate an ``EvoRouter`` from the declarative manifest definition.

    Args:
        router: The router instance to populate.
        manifest: Optional in-memory manifest mapping; useful for tests.
        manifest_path: Path override when reading from disk.

    Returns:
        The populated router instance (identical to the passed ``router``).

    Raises:
        ManifestError: If required fields are missing or handlers cannot be
            resolved.
    """

    manifest_data = manifest if manifest is not None else load_manifest(manifest_path)
    routes = manifest_data.get("routes")
    if routes is None:
        raise ManifestError("Manifest missing 'routes' section")
    if not isinstance(routes, Iterable):
        raise ManifestError("Manifest 'routes' section must be iterable")

    for entry in routes:
        _register_route(router, entry)

    return router


def _register_route(router: EvoRouter, entry: Any) -> None:
    if not isinstance(entry, Mapping):
        raise ManifestError("Each route entry must be a mapping")

    required_fields = {"id", "path", "method", "scope", "handler", "description"}
    missing = required_fields.difference(entry)
    if missing:
        raise ManifestError(f"Route entry missing required fields: {sorted(missing)}")

    handler = _resolve_handler(str(entry["handler"]))

    try:
        router.register(
            RouteSpec(
                id=str(entry["id"]),
                path=str(entry["path"]),
                method=str(entry["method"]).upper(),
                scope=str(entry["scope"]),
                handler=handler,
                description=str(entry["description"]),
                tags=tuple(str(tag) for tag in entry.get("tags", ()) if tag is not None),
            )
        )
    except ValueError as error:
        raise ManifestError(str(error)) from error


def _resolve_handler(handler_path: str) -> Any:
    module_path, _, attribute = handler_path.rpartition(".")
    if not module_path or not attribute:
        raise ManifestError(f"Invalid handler reference: '{handler_path}'")

    try:
        module = import_module(module_path)
    except ModuleNotFoundError as error:
        raise ManifestError(f"Cannot import handler module '{module_path}'") from error

    try:
        return getattr(module, attribute)
    except AttributeError as error:
        raise ManifestError(
            f"Handler attribute '{attribute}' not found in module '{module_path}'"
        ) from error
