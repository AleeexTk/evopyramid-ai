from pathlib import Path
import sys
import types


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


sys.modules.setdefault("requests", types.ModuleType("requests"))
pil_module = types.ModuleType("PIL")
pil_image_module = types.ModuleType("PIL.Image")
pil_module.Image = types.SimpleNamespace()
sys.modules.setdefault("PIL", pil_module)
sys.modules.setdefault("PIL.Image", pil_image_module)
flask_module = types.ModuleType("flask")
flask_module.Flask = type("Flask", (), {})
flask_module.jsonify = lambda *args, **kwargs: None
flask_module.request = types.SimpleNamespace()
sys.modules.setdefault("flask", flask_module)


def _fake_safe_load(stream: object) -> dict:
    if hasattr(stream, "read"):
        content = stream.read()
    else:
        content = stream
    result: dict = {}
    current_section: str | None = None
    for raw_line in str(content).splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if not line.startswith(" "):
            key = line.rstrip(":")
            result[key] = {}
            current_section = key
        elif current_section is not None:
            sub_key, value = line.strip().split(":", 1)
            value = value.strip()
            if value.lower() in {"true", "false"}:
                parsed_value: object = value.lower() == "true"
            else:
                try:
                    parsed_value = int(value)
                except ValueError:
                    parsed_value = value
            result[current_section][sub_key.strip()] = parsed_value
    return result


yaml_module = types.ModuleType("yaml")
yaml_module.safe_load = _fake_safe_load
sys.modules.setdefault("yaml", yaml_module)

from apps.core.evo_core import DEFAULT_CONFIG, load_config


def test_load_config_does_not_mutate_defaults(tmp_path: Path) -> None:
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
    config_without_overrides["logging"]["level"] = "WARNING"
    assert DEFAULT_CONFIG["logging"]["level"] == "INFO"
