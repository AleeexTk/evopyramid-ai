from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


def _build_stub_modules() -> dict[str, ModuleType]:
    """Create minimal stubs for optional evo_core dependencies."""

    stubs: dict[str, ModuleType] = {}

    requests_stub = ModuleType("requests")
    stubs["requests"] = requests_stub

    pil_stub = ModuleType("PIL")
    pil_image_stub = ModuleType("PIL.Image")
    pil_stub.Image = SimpleNamespace()
    stubs["PIL"] = pil_stub
    stubs["PIL.Image"] = pil_image_stub

    flask_stub = ModuleType("flask")
    flask_stub.Flask = type("Flask", (), {})
    flask_stub.jsonify = lambda *args, **kwargs: None
    flask_stub.request = SimpleNamespace()
    stubs["flask"] = flask_stub

    def _fake_safe_load(stream: object) -> dict[str, dict[str, object]]:
        if hasattr(stream, "read"):
            content = stream.read()
        else:
            content = stream

        result: dict[str, dict[str, object]] = {}
        section: str | None = None
        for raw_line in str(content).splitlines():
            line = raw_line.rstrip()
            if not line:
                continue
            if not line.startswith(" "):
                key = line.rstrip(":")
                result[key] = {}
                section = key
                continue
            if section is None:
                continue
            sub_key, value = line.strip().split(":", 1)
            value = value.strip()
            if value.lower() in {"true", "false"}:
                parsed: object = value.lower() == "true"
            else:
                try:
                    parsed = int(value)
                except ValueError:
                    parsed = value
            result[section][sub_key.strip()] = parsed
        return result

    yaml_stub = ModuleType("yaml")
    yaml_stub.safe_load = _fake_safe_load
    stubs["yaml"] = yaml_stub

    return stubs


@pytest.fixture()
def evo_core_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Import ``apps.core.evo_core`` with optional dependencies stubbed."""

    project_root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(project_root))

    stubs = _build_stub_modules()
    for name, module in stubs.items():
        monkeypatch.setitem(sys.modules, name, module)
    sys.modules.pop("apps.core.evo_core", None)
    module = importlib.import_module("apps.core.evo_core")
    yield module
    sys.modules.pop("apps.core.evo_core", None)


def test_load_config_does_not_mutate_defaults(
    evo_core_module: ModuleType, tmp_path: Path
) -> None:
    DEFAULT_CONFIG = evo_core_module.DEFAULT_CONFIG
    load_config = evo_core_module.load_config

    config_path = tmp_path / "config.yml"
    config_yaml = (
        "logging:\n"
        "  level: DEBUG\n"
        "server:\n"
        "  port: 6000\n"
        "  debug: true\n"
    )
    config_path.write_text(config_yaml, encoding="utf-8")

    config_with_overrides = load_config(str(config_path))
    assert config_with_overrides["logging"]["level"] == "DEBUG"
    assert config_with_overrides["server"]["port"] == 6000
    assert config_with_overrides["server"]["debug"] is True

    # Ensure the default configuration remains unchanged after loading overrides
    assert DEFAULT_CONFIG["logging"]["level"] == "INFO"
    assert DEFAULT_CONFIG["server"]["port"] == 5002
    assert DEFAULT_CONFIG["server"]["debug"] is False

    config_without_overrides = load_config()
    assert config_without_overrides == DEFAULT_CONFIG

    # Mutating the returned config should not affect DEFAULT_CONFIG
    mutated = load_config()
    mutated["logging"]["level"] = "WARNING"
    assert DEFAULT_CONFIG["logging"]["level"] == "INFO"
