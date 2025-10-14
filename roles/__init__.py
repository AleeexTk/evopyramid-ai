"""Top-level namespace for EvoPyramid role integrations."""

from importlib import import_module
from types import ModuleType

__all__ = ["load_role_module"]


def load_role_module(role_name: str) -> ModuleType:
    """Dynamically import a role package by name.

    Parameters
    ----------
    role_name:
        Dotted path of the role package relative to the ``roles`` namespace.

    Returns
    -------
    ModuleType
        The imported module.
    """

    return import_module(f"roles.{role_name}")
