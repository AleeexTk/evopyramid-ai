import json, os

def load_keys(path: str = "apps/core/keys/evo_keys.json") -> dict:
    if not os.path.exists(path):
        # используем sample как подсказку
        sample = os.path.join(os.path.dirname(path), "evo_keys.sample.json")
        if os.path.exists(sample):
            with open(sample, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
