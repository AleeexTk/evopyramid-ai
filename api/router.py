"""Lightweight router for EvoPyramid's internal API layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Optional


@dataclass(slots=True)
class RouteSpec:
    """Declarative description of an API route."""

    id: str
    path: str
    method: str
    scope: str
    handler: Callable[..., Any]
    description: str
    tags: tuple[str, ...] = field(default_factory=tuple)


class EvoRouter:
    """Registry of manifest-defined EvoPyramid API routes."""

    def __init__(self) -> None:
        self._routes: Dict[str, RouteSpec] = {}

    def register(self, spec: RouteSpec) -> None:
        """Register a new route.

        Raises:
            ValueError: if a route with the same id or path already exists.
        """

        if spec.id in self._routes:
            raise ValueError(f"Route id '{spec.id}' already registered")

        if any(existing.path == spec.path and existing.method == spec.method for existing in self._routes.values()):
            raise ValueError(f"Route path '{spec.method} {spec.path}' already registered")

        self._routes[spec.id] = spec

    def get(self, route_id: str) -> RouteSpec:
        """Return the route metadata for the given identifier."""

        try:
            return self._routes[route_id]
        except KeyError as error:  # pragma: no cover - defensive guard
            raise KeyError(f"Route '{route_id}' is not registered") from error

    def resolve(self, path: str, method: str) -> Optional[RouteSpec]:
        """Return the route spec that matches the provided path and method."""

        method_upper = method.upper()
        for spec in self._routes.values():
            if spec.path == path and spec.method == method_upper:
                return spec
        return None

    def routes(self) -> Iterable[RouteSpec]:
        """Iterate over all registered routes."""

        return self._routes.values()

    def dispatch(self, route_id: str, *args: Any, **kwargs: Any) -> Any:
        """Execute the handler associated with a registered route."""

        spec = self.get(route_id)
        return spec.handler(*args, **kwargs)
