"""Tests for the HierarchicalPyramidMemory caching behaviour."""

import copy
import sys
import types


if "requests" not in sys.modules:
    requests_stub = types.ModuleType("requests")

    class _RequestException(Exception):
        """Fallback requests exception for tests."""

    def _noop_get(*_args, **_kwargs):  # noqa: D401 - trivial stub
        return None

    requests_stub.get = _noop_get
    requests_stub.RequestException = _RequestException
    sys.modules["requests"] = requests_stub

if "flask" not in sys.modules:
    flask_stub = types.ModuleType("flask")

    class _Flask:
        """Minimal Flask stub for tests."""

        def __init__(self, *_args, **_kwargs) -> None:  # noqa: D401 - trivial stub
            pass

        def route(self, *_args, **_kwargs):  # noqa: D401 - trivial stub
            def decorator(func):
                return func

            return decorator

    def _jsonify(*_args, **_kwargs):  # noqa: D401 - trivial stub
        return {}

    flask_stub.Flask = _Flask
    flask_stub.jsonify = _jsonify
    flask_stub.request = types.SimpleNamespace(method="GET", json=None)
    sys.modules["flask"] = flask_stub

if "PIL" not in sys.modules:
    pil_stub = types.ModuleType("PIL")
    pil_image_stub = types.ModuleType("PIL.Image")

    def _image_open(*_args, **_kwargs):  # noqa: D401 - trivial stub
        raise NotImplementedError("PIL.Image.open is not available in tests")

    pil_image_stub.open = _image_open
    pil_image_stub.Image = type("Image", (), {})
    pil_stub.Image = pil_image_stub
    sys.modules["PIL"] = pil_stub
    sys.modules["PIL.Image"] = pil_image_stub

from apps.core.evo_core import DEFAULT_CONFIG, HierarchicalPyramidMemory


def test_query_memory_uses_cache(tmp_path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    config = copy.deepcopy(DEFAULT_CONFIG)
    memory = HierarchicalPyramidMemory(str(log_dir), config)

    content = {"value": "cached result", "priority": "high"}
    tags = ["Cache", "Behaviour", "Memory"]

    node_id = memory.save_memory(content, tags, "test", affective_score=0.9)
    assert node_id is not None

    query = "cache behaviour memory"
    first_results = memory.query_memory(query)
    assert first_results

    cache_key = memory._build_cache_key_from_query(query)
    assert cache_key in memory.cache

    memory.nodes.clear()

    second_results = memory.query_memory(query)
    assert second_results == first_results
