import argparse
import asyncio
import json
from typing import Any, Dict

from apps.bridge.evonexus.nexus import EvoNexusBridge


def _pretty(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


async def main() -> int:
    parser = argparse.ArgumentParser(description="EvoNexusBridge CLI")
    parser.add_argument("--proposal", required=True, help="Текст предложения / намерения")
    parser.add_argument("--session", default="PEAR_A24", help="ID сессии")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (детерминизм)")
    args = parser.parse_args()

    bridge = EvoNexusBridge()
    result = await bridge.run(proposal=args.proposal, session_id=args.session, seed=args.seed)

    print("\n=== 🧬 EvoNexusBridge → Consensus ===")
    print(f"Session: {result['session_id']} | Proposal: {args.proposal}")
    print(f"Priority Path: {result['context'].get('priority_path', 'HYBRID')}")
    print(
        "Emotion: {} | Urgency: {:.2f}".format(
            result["fusion"]["signals"].get("emotion"), result["fusion"]["signals"].get("urgency")
        )
    )
    print(f"Density: {result['fusion']['density']:.2f}")
    print(
        "Decision: {} | State: {} | Consensus: {:.2f}".format(
            result["verdict"]["decision"], result["verdict"]["state"], result["verdict"]["consensus"]
        )
    )
    print("\n-- Insight --")
    print(result["fusion"]["insight"])
    print("\n-- Creative Output --")
    print(result["fusion"]["creative_output"])
    print("\n-- Votes --")
    print(_pretty(result["verdict"]["votes"]))
    print("\n(Артефакт сохранён в EVODIR/nexus_logs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
