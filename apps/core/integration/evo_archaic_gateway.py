"""EvoMethod_SK archaic session gateway utilities."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

import yaml


class EvoArchaicGateway:
    """Convert historical Evo sessions into structured containers."""

    def __init__(self, input_dir: str = "Download/Evo/Входящие_Контейнеры") -> None:
        self.input_dir = Path(input_dir)
        self.output_dir = Path("containers/archeology")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def detect_session_structure(self, content: str) -> str:
        """Determine session type (SK1/SK2) based on density heuristics."""
        lines = content.splitlines()
        word_count = sum(len(line.split()) for line in lines)

        if word_count > 1000 or "архитектура" in content.lower():
            return "SK2"
        return "SK1"

    def convert_to_container(self, filename: str, content: str) -> dict:
        """Convert raw text into a structured container payload."""
        session_type = self.detect_session_structure(content)

        container = {
            "metadata": {
                "container_id": f"archeo_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "original_filename": filename,
                "session_type": session_type,
                "import_timestamp": datetime.now().isoformat(),
                "evo_method": f"Evo_method_SK_{session_type}",
            },
            "content": {
                "raw_text": content,
                "summary": content[:500] + "..." if len(content) > 500 else content,
            },
            "color_blocks": self.extract_color_blocks(content),
            "anchors": self.extract_anchors(content),
        }

        return container

    def extract_color_blocks(self, content: str) -> List[dict]:
        """Extract simplified color blocks from session content."""
        blocks = []
        sentences = content.split(". ")

        for index, sentence in enumerate(sentences[:10]):
            lower_sentence = sentence.lower()
            if any(word in lower_sentence for word in ["определение", "концепция", "базов"]):
                color = "yellow"
            elif any(word in lower_sentence for word in ["ошибка", "конфликт", "проблема"]):
                color = "red"
            elif any(word in lower_sentence for word in ["стратегия", "план", "решение"]):
                color = "green"
            elif any(word in lower_sentence for word in ["данные", "метрика", "факт"]):
                color = "blue"
            else:
                color = "orange"

            blocks.append(
                {
                    "block_id": f"B{index:03d}",
                    "color": color,
                    "content": sentence,
                    "shade": "light" if len(sentence) < 100 else "dark",
                }
            )

        return blocks

    def extract_anchors(self, content: str) -> List[str]:
        """Extract simplified keyword anchors from the content."""
        words = content.lower().split()
        keywords = [word for word in words if len(word) > 5 and word.isalpha()]
        return list(dict.fromkeys(keywords))[:5]

    def process_archaic_sessions(self) -> List[str]:
        """Process input directory and generate containers for each session."""
        containers_created: List[str] = []

        for file_path in self.input_dir.glob("*.txt"):
            try:
                content = file_path.read_text(encoding="utf-8")
                container = self.convert_to_container(file_path.name, content)

                output_file = self.output_dir / f"{container['metadata']['container_id']}.yaml"
                with output_file.open("w", encoding="utf-8") as file_descriptor:
                    yaml.dump(container, file_descriptor, allow_unicode=True, default_flow_style=False)

                containers_created.append(container["metadata"]["container_id"])
                print(f"✅ Создан контейнер: {output_file}")
            except Exception as exc:  # pylint: disable=broad-exception-caught
                print(f"❌ Ошибка обработки {file_path}: {exc}")

        return containers_created


def main() -> None:
    gateway = EvoArchaicGateway()
    results = gateway.process_archaic_sessions()
    print(f"Обработано сессий: {len(results)}")


if __name__ == "__main__":
    main()
