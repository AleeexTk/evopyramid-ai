"""Laboratory adapters for EvoAbsolute."""

from pathlib import Path

LAB_HOME = Path(__file__).parent
EVOFINART_ROOT = LAB_HOME / "EvoFinArt"

__all__ = ["LAB_HOME", "EVOFINART_ROOT"]
