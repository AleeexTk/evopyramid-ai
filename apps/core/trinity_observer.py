import asyncio, os, json
from datetime import datetime
from typing import Dict, Any, List

REPORT_DIR = "codex_feedback"
LOG_PATH = "logs/codex_feedback.log"

class TrinityObserver:
    def __init__(self):
        os.makedirs(REPORT_DIR, exist_ok=True)

    async def scan(self) -> Dict[str, Any]:
        # здесь можно дополнять метриками из FlowMonitor / CollectiveMind
        return {
            "ts": datetime.utcnow().isoformat() + "Z",
            "repo_state": "observed",
            "signals": {
                "lint": self._probe_file_exists(".ruff.toml") or self._probe_file_exists("pyproject.toml"),
                "tests_dir": self._probe_dir_exists("tests"),
            }
        }

    def codex_feedback(self) -> Dict[str, Any]:
        if not os.path.exists(LOG_PATH):
            return {"codex_feedback": ["No feedback yet."]}
        try:
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()[-10:]
            return {"codex_feedback": [l.rstrip("\n") for l in lines]}
        except Exception as e:
            return {"codex_feedback_error": str(e)}

    def _probe_file_exists(self, path: str) -> bool:
        return os.path.isfile(path)

    def _probe_dir_exists(self, path: str) -> bool:
        return os.path.isdir(path)

    def _save_report(self, payload: Dict[str, Any]) -> str:
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        out = os.path.join(REPORT_DIR, f"trinity_report_{ts}.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return out

async def main(pause_sec: int = 600):
    observer = TrinityObserver()
    while True:
        status = await observer.scan()
        feedback = observer.codex_feedback()
        merged = {**status, **feedback}
        path = observer._save_report(merged)
        print(f"[Trinity] report saved → {path}")
        await asyncio.sleep(pause_sec)

if __name__ == "__main__":
    asyncio.run(main())
