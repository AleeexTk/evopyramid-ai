"""Context utilities exposed for EvoLocalContext."""
from .device_analyzer import analyze_device
from .environment_detector import detect_environment
from .local_sync_manager import mark_local_request

__all__ = ["analyze_device", "detect_environment", "mark_local_request"]
