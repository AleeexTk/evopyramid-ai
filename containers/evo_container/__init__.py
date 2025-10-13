"""Self-processing container prototype for EvoPyramid."""

from importlib import import_module
from typing import Any, Callable, Dict, Iterable, List, MutableMapping

PipelineStep = Dict[str, Any]


def load_step_callable(step: PipelineStep) -> Callable[[MutableMapping[str, Any]], None]:
    """Resolve a pipeline step into an executable callable.

    The manifest stores dotted module paths and an optional function name.
    This helper performs the import dynamically and returns a callable that
    accepts a mutable context dictionary.
    """

    module_path = step["module"]
    function_name = step.get("function", "run")
    module = import_module(module_path)
    try:
        return getattr(module, function_name)
    except AttributeError as exc:  # pragma: no cover - defensive guard
        raise AttributeError(
            f"Pipeline step {module_path}.{function_name} is not available"
        ) from exc


__all__ = ["PipelineStep", "load_step_callable"]
