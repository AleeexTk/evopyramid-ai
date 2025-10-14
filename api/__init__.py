"""EvoPyramid API package.

This module exposes the lightweight routing layer that binds internal
laboratories, digital souls, and external bridges through a unified
manifest-driven protocol.
"""

from .bootstrap import ManifestError, bootstrap_router_from_manifest, load_manifest
from .router import EvoRouter, RouteSpec

__all__ = [
    "EvoRouter",
    "RouteSpec",
    "ManifestError",
    "load_manifest",
    "bootstrap_router_from_manifest",
]
