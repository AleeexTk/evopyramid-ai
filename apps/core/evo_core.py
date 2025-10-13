"""EvoMetaCore application module.

This module implements the EvoMetaCore digital organism along with a
Flask API for interacting with it. The architecture is intentionally
modular so that each subsystem can evolve independently while still
operating as part of a cohesive organism.
"""
from __future__ import annotations

import asyncio
import base64
import copy
import hashlib
import io
import json
import logging
import os
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Coroutine
from uuid import uuid4

try:  # pragma: no cover - optional dependency
    import requests
    RequestException = requests.RequestException
except ImportError:  # pragma: no cover - optional dependency fallback
    requests = None  # type: ignore[assignment]

    class RequestException(Exception):
        """Fallback exception used when ``requests`` is unavailable."""

        pass
import yaml
from flask import Flask, jsonify, request
from PIL import Image

try:  # pragma: no cover - fallback path is covered by unit tests
    from apps.core.integration.context_engine import get_context_engine
except ImportError:  # pragma: no cover - allows running without optional deps
    get_context_engine = None  # type: ignore[assignment]

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from apps.core.integration.context_engine import EvoCodexContextEngine


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "logging": {
        "base_dir": os.path.join(os.environ.get("HOME", "."), "Documents", "EVO"),
        "level": "INFO",
    },
    "memory": {
        "auto_delete_threshold": 30,
    },
    "server": {
        "host": "0.0.0.0",
        "port": 5002,
        "debug": False,
        "use_reloader": False,
    },
}


def _deep_update(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively update ``base`` with values from ``updates``."""

    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        elif isinstance(value, dict):
            base[key] = copy.deepcopy(value)
        else:
            base[key] = value
    return base


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load YAML configuration if available, otherwise use defaults."""

    config = copy.deepcopy(DEFAULT_CONFIG)

    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as cfg_file:
            loaded = yaml.safe_load(cfg_file) or {}
        return _deep_update(config, loaded)

    return config


# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------


def configure_logging(config: Dict[str, Any]) -> str:
    """Configure logging according to the supplied configuration."""

    base_dir = config["logging"].get("base_dir", DEFAULT_CONFIG["logging"]["base_dir"])
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"EvoMetaLog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    logging.basicConfig(
        level=getattr(logging, config["logging"].get("level", "INFO")),
        format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode="a", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    return log_dir


logger = logging.getLogger("Evo.MetaCore")


# ---------------------------------------------------------------------------
# Memory subsystem
# ---------------------------------------------------------------------------


class MemoryNode:
    """Represents a single node within the hierarchical pyramid memory."""

    def __init__(
        self,
        node_id: str,
        level: int,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.id = node_id
        self.level = level
        self.content = content
        self.metadata = metadata or {
            "created_at": int(time.time()),
            "last_access": int(time.time()),
            "relevance": 0.5,
            "source": "EVO",
            "tags": [],
            "parent_ids": [],
            "child_ids": [],
            "link_weight": "essential",
            "affective_score": 0.5,
        }
        self.metadata["signature"] = self._generate_signature(content)
        logger.debug("Создан узел памяти %s (уровень %s)", self.id, self.level)

    def _generate_signature(self, content: Dict[str, Any]) -> str:
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode("utf-8")).hexdigest()

    def verify_signature(self) -> bool:
        return self.metadata["signature"] == self._generate_signature(self.content)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "level": self.level,
            "content": self.content,
            "metadata": self.metadata,
        }


class HierarchicalPyramidMemory:
    """Hierarchical memory that stores sensory data, insights, and goals."""

    def __init__(self, log_dir: str, config: Dict[str, Any]) -> None:
        self.nodes: Dict[str, MemoryNode] = {}
        self.auto_delete_threshold = config["memory"].get(
            "auto_delete_threshold", DEFAULT_CONFIG["memory"]["auto_delete_threshold"]
        )
        self.archive_dir = os.path.join(log_dir, "archive")
        os.makedirs(self.archive_dir, exist_ok=True)
        self.cache: Dict[tuple, List[Dict[str, Any]]] = {}
        self.patterns: Dict[tuple, int] = {}
        logger.info("HierarchicalPyramidMemory: инициализирована.")

    def save_memory(
        self,
        content: Dict[str, Any],
        tags: List[str],
        memory_type: str,
        level: int = 0,
        parent_id: Optional[str] = None,
        link_weight: str = "essential",
        affective_score: float = 0.5,
    ) -> Optional[str]:
        node_id = f"memory_{uuid4().hex[:8]}"
        relevance_score = self._calculate_relevance(tags, affective_score, content)
        metadata = {
            "tags": tags,
            "relevance": relevance_score,
            "source": memory_type,
            "parent_ids": [parent_id] if parent_id else [],
            "child_ids": [],
            "link_weight": link_weight,
            "affective_score": affective_score,
        }
        node = MemoryNode(node_id, level, content, metadata)
        if not node.verify_signature():
            logger.error("Узел %s не прошёл проверку подписи", node_id)
            return None
        self.nodes[node_id] = node
        if parent_id and parent_id in self.nodes:
            self.nodes[parent_id].metadata.setdefault("child_ids", []).append(node_id)
        if relevance_score >= 0.8:
            cache_key = self._build_cache_key_from_tags(tags)
            if cache_key:
                self.cache.setdefault(cache_key, [])
                self.cache[cache_key].append(node.to_dict())
        self._update_patterns(tags)
        logger.info(
            "Сохранён узел памяти %s (уровень %s, тип %s)", node_id, level, memory_type
        )
        return node_id

    def _update_patterns(self, tags: List[str]) -> None:
        tag_key = tuple(sorted(tags))
        self.patterns[tag_key] = self.patterns.get(tag_key, 0) + 1
        logger.debug("Обновлён паттерн %s → %s", tag_key, self.patterns[tag_key])

    def predict_next_action(self, query: str) -> Optional[str]:
        query_tags = query.lower().split()
        max_freq = 0
        predicted_action = None
        for pattern_tags, freq in self.patterns.items():
            if any(tag in pattern_tags for tag in query_tags) and freq > max_freq:
                max_freq = freq
                predicted_action = f"Предсказано действие для тегов {pattern_tags}"
        if predicted_action:
            logger.info("Предсказательное действие: %s (частота %s)", predicted_action, max_freq)
        return predicted_action

    def query_memory(
        self,
        query: str,
        level: Optional[int] = None,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        cache_key = self._build_cache_key_from_query(query)
        if use_cache and cache_key in self.cache:
            return [copy.deepcopy(item) for item in self.cache[cache_key]]
        results: List[Dict[str, Any]] = []
        high_relevance_results: List[Dict[str, Any]] = []
        query_tokens = self._tokenise_query(query)
        for node in self.nodes.values():
            if level is not None and node.level != level:
                continue
            tags = node.metadata.get("tags", [])
            tag_tokens = [tag.lower() for tag in tags]
            if (query_tokens & set(tag_tokens) or any(tag in query.lower() for tag in tag_tokens)) and node.verify_signature():
                node_dict = node.to_dict()
                results.append(node_dict)
                node.metadata["last_access"] = int(time.time())
                if node.metadata.get("relevance", 0.0) >= 0.8:
                    high_relevance_results.append(node_dict)
        if high_relevance_results and cache_key:
            self.cache[cache_key] = [copy.deepcopy(item) for item in high_relevance_results]
        return results

    def _calculate_relevance(
        self,
        tags: List[str],
        affective_score: float,
        content: Optional[Dict[str, Any]] = None,
    ) -> float:
        tag_boost = min(0.4, 0.05 * len({tag.lower() for tag in tags if tag}))
        affective_adjustment = (max(0.0, min(1.0, affective_score)) - 0.5) * 0.6
        urgency_hint = 0.0
        if content:
            urgency_hint = 0.1 if content.get("priority") == "high" else 0.0
        relevance = 0.5 + tag_boost + affective_adjustment + urgency_hint
        return max(0.0, min(1.0, relevance))

    def _build_cache_key_from_tags(self, tags: List[str]) -> tuple:
        normalised_tags = tuple(sorted({tag.lower() for tag in tags if tag}))
        return normalised_tags

    def _build_cache_key_from_query(self, query: str) -> tuple:
        return tuple(sorted(self._tokenise_query(query)))

    def _tokenise_query(self, query: str) -> set:
        return {token for token in query.lower().split() if token}

    def quantum_leap(self, node_id1: str, node_id2: str) -> Optional[Dict[str, Any]]:
        if node_id1 not in self.nodes or node_id2 not in self.nodes:
            return None
        first = self.nodes[node_id1]
        second = self.nodes[node_id2]
        if not (first.verify_signature() and second.verify_signature()):
            logger.error("Квантовый скачок отклонён: подписи не совпадают")
            return None
        if random.random() < 0.1:
            new_content = {**first.content, **second.content, "merged_at": int(time.time())}
            new_level = max(first.level, second.level) + 1
            new_tags = list(set(first.metadata["tags"] + second.metadata["tags"] + ["quantum_leap"]))
            new_affective_score = (first.metadata["affective_score"] + second.metadata["affective_score"]) / 2
            new_node_id = self.save_memory(
                new_content,
                new_tags,
                "quantum_leap",
                new_level,
                parent_id=node_id1,
                link_weight="optional",
                affective_score=new_affective_score,
            )
            if new_node_id:
                logger.info(
                    "Квантовый скачок: %s + %s → %s", node_id1, node_id2, new_node_id
                )
                return self.nodes[new_node_id].to_dict()
        return None

    def archive(self, node_id: str) -> None:
        if node_id not in self.nodes:
            return
        node = self.nodes[node_id]
        if (
            not node.metadata.get("child_ids")
            and not node.metadata.get("parent_ids")
            and node.metadata.get("relevance", 0.0) < 0.3
        ):
            archive_path = os.path.join(self.archive_dir, f"node_{node_id}.json")
            with open(archive_path, "w", encoding="utf-8") as archive_file:
                json.dump(node.to_dict(), archive_file, indent=2, ensure_ascii=False)
            del self.nodes[node_id]
            self.cache.pop(node_id, None)
            logger.info("Узел %s архивирован в %s", node_id, archive_path)

    def cleanup(self) -> None:
        now = time.time()
        for node_id in list(self.nodes):
            node = self.nodes[node_id]
            if now - node.metadata.get("last_access", now) > self.auto_delete_threshold:
                self.archive(node_id)
        logger.info("Очистка памяти завершена.")

    def to_xml(self) -> str:
        """Serialise the current memory pyramid to XML."""

        import xml.etree.ElementTree as ET

        root = ET.Element("MemoryPyramid")
        for node in self.nodes.values():
            node_element = ET.SubElement(root, "MemoryNode", id=node.id, level=str(node.level))
            content = ET.SubElement(node_element, "Content")
            for key, value in node.content.items():
                item = ET.SubElement(content, "Item", key=str(key))
                item.text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
            metadata = ET.SubElement(node_element, "Metadata")
            for key, value in node.metadata.items():
                item = ET.SubElement(metadata, "Item", key=str(key))
                item.text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
        return ET.tostring(root, encoding="unicode")


# ---------------------------------------------------------------------------
# Additional subsystems
# ---------------------------------------------------------------------------


class ContainerOrchestrator:
    def __init__(self, core: "EvoMetaCore") -> None:
        self.core = core
        self.contexts: Dict[str, Dict[str, Any]] = {}
        self.replicas: List[EvoMetaCore] = [self.core]
        self.remote_pyramids: Dict[str, str] = {}
        logger.info("ContainerOrchestrator: инициализирован.")

    def distribute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        selected_core = self.core
        if len(self.replicas) > 1:
            active_replicas = [replica for replica in self.replicas if replica.is_running]
            if active_replicas:
                selected_core = random.choice(active_replicas)
        context_id = f"context_{uuid4().hex[:8]}"
        self.contexts[context_id] = {"task": task, "status": "pending"}
        try:
            result = selected_core.process_task(task)
            self.contexts[context_id]["status"] = "completed"
            self.contexts[context_id]["result"] = result
        except Exception as exc:  # noqa: BLE001
            logger.exception("Ошибка в ядре при обработке %s: %s", context_id, exc)
            self.contexts[context_id]["status"] = "failed"
            self.contexts[context_id]["result"] = {"status": "failed", "reason": str(exc)}
            return self.contexts[context_id]["result"]
        logger.info("Задача %s обработана ядром.", context_id)
        return result

    def add_replica(self, core: "EvoMetaCore") -> None:
        self.replicas.append(core)
        logger.info("Добавлена новая реплика ядра.")

    def connect_remote_pyramid(self, address: str, pyramid_id: str) -> None:
        if requests is None:
            logger.warning(
                "Requests недоступен: пропускаем подключение пирамиды %s", pyramid_id
            )
            return

        try:
            response = requests.get(f"{address}/api/get_pyramid", timeout=5)
            response.raise_for_status()
            self.remote_pyramids[pyramid_id] = response.text
            logger.info("Подключена внешняя пирамида %s", pyramid_id)
        except RequestException as exc:
            logger.error("Ошибка подключения пирамиды %s: %s", pyramid_id, exc)


class DataAssimilationNexus:
    def __init__(self, core: "EvoMetaCore") -> None:
        self.core = core
        logger.info("DataAssimilationNexus: инициализирован.")

    def process_multimodal_input(self, raw_data: Any, input_type: str = "text") -> Dict[str, Any]:
        logger.info("DataAssimilationNexus: обработка данных типа %s", input_type)
        data_hash = hash(str(raw_data))
        emotion_level = (data_hash % 100) / 100.0
        tags = [f"input_{input_type}", f"hash_{data_hash}"]
        content: Dict[str, Any] = {}

        if input_type == "text":
            content = {"value": str(raw_data)}
            if isinstance(raw_data, str):
                tags.extend(raw_data.lower().split()[:3])
        elif input_type == "image":
            try:
                img_data = base64.b64decode(raw_data.split(",")[1] if "," in raw_data else raw_data)
                img = Image.open(io.BytesIO(img_data))
                width, height = img.size
                content = {"width": width, "height": height, "format": img.format}
                tags.extend(["image", f"size_{width}x{height}"])
            except Exception as exc:  # noqa: BLE001
                logger.error("Ошибка обработки изображения: %s", exc)
                content = {"error": str(exc)}
                tags.append("error")
        else:
            content = {"value": raw_data}

        sense_packet = {
            "id": f"sense_{uuid4().hex[:8]}",
            "source": "multimodal_sensor",
            "timestamp": datetime.now().isoformat(),
            "content": content,
            "emotional_tone": emotion_level,
            "associated_tags": list(set(tags)),
            "input_type": input_type,
        }
        node_id = self.core.memory_manager.save_memory(
            sense_packet,
            sense_packet["associated_tags"],
            "sensory",
            level=0,
            affective_score=emotion_level,
        )
        logger.debug("Создан сенсорный пакет %s (узел %s)", sense_packet["id"], node_id)
        self.core.emotional_palette.analyze_emotional_tone(sense_packet)
        return sense_packet


class SelfAwarenessCore:
    def __init__(self, core: "EvoMetaCore") -> None:
        self.core = core
        self.internal_metrics: Dict[str, Any] = {}
        self.anomaly_threshold = 0.95
        logger.info("SelfAwarenessCore: инициализировано.")

    def update_metrics(self) -> None:
        self.internal_metrics = {
            "timestamp": time.time(),
            "coherence_level": random.uniform(0.8, 1.0),
            "memory_usage": len(self.core.memory_manager.nodes),
        }

    def analyze_state(self) -> str:
        self.update_metrics()
        coherence = self.internal_metrics["coherence_level"]
        if coherence < self.anomaly_threshold:
            self.core.role_evolution_engine.evolve_roles("кризис и самокоррекция")
            return f"⚠️ Аномалия! Когерентность: {coherence:.2f}. Эволюция ролей запущена."
        return f"✅ Состояние стабильно. Когерентность: {coherence:.2f}."


class EmotionalPalette:
    def __init__(self, core: "EvoMetaCore") -> None:
        self.core = core
        self.current_mood = "calm"
        self.emotion_map = {
            "calm": 0.5,
            "curious": 0.7,
            "anxious": 0.3,
            "inspired": 0.9,
            "conflicted": 0.4,
        }
        self.affective_map: Dict[str, Dict[str, Any]] = {}
        logger.info("EmotionalPalette: инициализирована.")

    def analyze_emotional_tone(self, sense_packet: Dict[str, Any]) -> str:
        emotion_level = sense_packet.get("emotional_tone", 0.5)
        node_id = sense_packet.get("id")
        associated_tags = sense_packet.get("associated_tags", [])
        if emotion_level > 0.8:
            self.current_mood = "inspired"
        elif emotion_level > 0.6:
            self.current_mood = "curious"
        elif emotion_level < 0.4:
            self.current_mood = "anxious"
        elif "конфликт" in associated_tags or "error" in associated_tags:
            self.current_mood = "conflicted"
        else:
            self.current_mood = "calm"
        self.affective_map[node_id] = {"mood": self.current_mood, "score": emotion_level}
        logger.info("EmotionalPalette: текущее настроение %s (%.2f)", self.current_mood, emotion_level)
        return self.current_mood

    def get_mood_modifier(self) -> float:
        return self.emotion_map.get(self.current_mood, 0.5)

    def get_affective_map(self) -> Dict[str, Dict[str, Any]]:
        return self.affective_map


class CreativeEngine:
    def __init__(self, core: "EvoMetaCore") -> None:
        self.core = core
        logger.info("CreativeEngine: инициализирован.")

    def generate_creative_insight(self, fused_insight: Dict[str, Any]) -> Dict[str, Any]:
        input_context = fused_insight.get("input_context", {})
        emotional_influence = fused_insight.get("emotional_influence", 0.5)
        base_words = input_context.get("content", {}).get("value", "").split() or ["смысл", "эволюция"]
        word1 = random.choice(base_words)
        associated_tags = input_context.get("associated_tags", ["идея"])
        word2 = random.choice(associated_tags)
        if emotional_influence > 0.8:
            metaphor = f"Это как {word1} и {word2}, танцующие в квантовом вихре!"
        else:
            metaphor = f"{word1} + {word2} = новое решение."
        creative_result = {
            "id": f"creative_{uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat(),
            "metaphor": metaphor,
            "emotional_root": emotional_influence,
        }
        self.core.memory_manager.save_memory(
            creative_result,
            ["creative", "metaphor"],
            "creative_output",
            level=1,
            affective_score=emotional_influence,
        )
        return creative_result


class CognitiveFusionMatrix:
    def __init__(self, core: "EvoMetaCore") -> None:
        self.core = core
        logger.info("CognitiveFusionMatrix: инициализирована.")

    def fuse_data(self, sense_packet: Dict[str, Any]) -> Dict[str, Any]:
        related_memories = self.core.memory_manager.query_memory(
            " ".join(sense_packet["associated_tags"]),
            level=0,
        )
        emotional_modifier = self.core.emotional_palette.get_mood_modifier()
        content = sense_packet.get("content", {})
        insight_text = f"Обработан {sense_packet['input_type']}: {content.get('value', content)}"
        predicted_action = self.core.memory_manager.predict_next_action(
            " ".join(sense_packet["associated_tags"])
        )
        final_insight = {
            "id": f"insight_{uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat(),
            "input_context": sense_packet,
            "fused_insight": insight_text,
            "related_memories_count": len(related_memories),
            "emotional_influence": emotional_modifier,
            "predicted_action": predicted_action,
        }
        creative_output = self.core.creative_engine.generate_creative_insight(final_insight)
        final_insight["creative_output"] = creative_output
        self.core.memory_manager.save_memory(
            final_insight,
            ["insight", "fusion"],
            "insight",
            level=1,
            parent_id=sense_packet["id"],
            affective_score=emotional_modifier,
        )
        if final_insight["emotional_influence"] < 0.6:
            self.core.role_evolution_engine.evolve_roles("нужен инновационный подход")
        return final_insight


class HierarchicalGoalPyramid:
    def __init__(self, core: "EvoMetaCore") -> None:
        self.core = core
        self.goals: Dict[str, Dict[str, Any]] = {}
        self.current_goal_id: Optional[str] = None
        self.goal_counter = 0
        logger.info("HierarchicalGoalPyramid: инициализирована.")

    def add_goal(self, description: str, priority: int = 1) -> str:
        self.goal_counter += 1
        goal_id = f"goal_{self.goal_counter}"
        new_goal = {
            "description": description,
            "priority": priority,
            "status": "active",
            "created_at": datetime.now().isoformat(),
        }
        self.goals[goal_id] = new_goal
        self.core.memory_manager.save_memory(new_goal, ["goal", f"priority_{priority}"], "goal", level=2)
        return goal_id

    def select_next_goal(self) -> Optional[Dict[str, Any]]:
        active_goals = [goal for goal in self.goals.values() if goal["status"] == "active"]
        if not active_goals:
            return None
        next_goal = max(active_goals, key=lambda goal: goal["priority"])
        self.current_goal_id = next(
            goal_id for goal_id, goal in self.goals.items() if goal is next_goal
        )
        return next_goal


class RoleEvolutionEngine:
    def __init__(self, core: "EvoMetaCore") -> None:
        self.core = core
        self.roles: Dict[str, Dict[str, bool]] = {
            "Innovator": {"active": True},
            "DataScientist": {"active": False},
        }
        logger.info("RoleEvolutionEngine: инициализирован.")

    def evolve_roles(self, context: str) -> None:
        lowered = context.lower()
        if "творчество" in lowered or "инновационный" in lowered:
            self.roles["Innovator"] = {"active": True}
            logger.info("RoleEvolutionEngine: активирована роль Innovator")
        elif "анализ" in lowered:
            self.roles["DataScientist"] = {"active": True}
            logger.info("RoleEvolutionEngine: активирована роль DataScientist")


class InterfaceAdapter:
    def __init__(self, core: "EvoMetaCore") -> None:
        self.core = core
        logger.info("InterfaceAdapter: инициализирован.")

    def render_output(self, insight: Dict[str, Any], output_format: str = "text") -> str:
        fused_insight = insight.get("fused_insight", "Инсайт не найден.")
        creative = insight.get("creative_output", {})
        metaphor = creative.get("metaphor", "Творческий инсайт отсутствует.")
        emotional_tone = insight.get("emotional_influence", 0.5)
        predicted_action = insight.get("predicted_action", "Предсказание отсутствует.")

        if output_format == "text":
            greeting = "😎 Grok на связи!" if emotional_tone > 0.8 else "Grok думает..."
            return "\n".join([greeting, fused_insight, metaphor, f"Предсказание: {predicted_action}"])

        if output_format == "api_response":
            return json.dumps(
                {
                    "status": "success",
                    "insight": fused_insight,
                    "metaphor": metaphor,
                    "predicted_action": predicted_action,
                },
                ensure_ascii=False,
                indent=2,
            )

        if output_format == "memory_graph":
            memory_nodes = self.core.memory_manager.query_memory(
                " ".join(insight.get("input_context", {}).get("associated_tags", []))
            )
            graph = {
                "nodes": memory_nodes,
                "affective_map": self.core.emotional_palette.get_affective_map(),
            }
            return json.dumps(graph, ensure_ascii=False, indent=2)

        if output_format == "xml":
            return self.core.memory_manager.to_xml()

        return "Неизвестный формат."


class EthicsCore:
    def __init__(self, core: "EvoMetaCore") -> None:
        self.core = core
        self.ethical_principles = {"harm_prevention": 1.0, "transparency": 0.8}
        logger.info("EthicsCore: инициализирован.")

    def check_action_ethics(self, action_type: str, action_details: Any) -> bool:
        details_str = str(action_details).lower()
        if "удаление" in action_type.lower() and "критические" in details_str:
            logger.warning("EthicsCore: опасное действие отклонено")
            return False
        if "атака" in details_str or "взлом" in details_str:
            logger.critical("EthicsCore: критически опасное действие отклонено")
            return False
        return True


class ActionEngine:
    def __init__(self, core: "EvoMetaCore") -> None:
        self.core = core
        logger.info("ActionEngine: инициализирован.")

    def execute_action(self, insight: Dict[str, Any], target_goal: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        input_context = insight.get("input_context", {})
        action_type = input_context.get("type", "generic")
        action_details = input_context.get("content", "Нет данных для действия")

        if not self.core.ethics_core.check_action_ethics(action_type, action_details):
            logger.error("ActionEngine: действие %s отклонено", action_type)
            return {"status": "failed", "reason": "Этический конфликт"}

        try:
            if action_type == "api_call" and isinstance(action_details, dict):
                if requests is None:
                    result = {
                        "status": "failed",
                        "reason": "requests_dependency_unavailable",
                    }
                else:
                    url = action_details.get("value", {}).get("url", "http://example.com")
                    payload = action_details.get("value", {}).get("payload", {})
                    response = requests.post(url, json=payload, timeout=5)
                    response.raise_for_status()
                    result = {"status": "success", "response": response.json()}
            elif action_type == "file_write":
                content = action_details.get("value", str(action_details)) if isinstance(action_details, dict) else str(action_details)
                file_path = os.path.join(self.core.log_dir, f"action_{uuid4().hex[:8]}.txt")
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(content)
                result = {"status": "success", "file": file_path}
            elif action_type == "image_analysis":
                result = {"status": "success", "message": f"Анализ изображения: {action_details}"}
            else:
                result = {"status": "success", "message": f"Имитация действия: {action_details}"}
            logger.info("Выполнено действие %s: %s", action_type, result)
        except RequestException as exc:
            logger.error("Ошибка при выполнении HTTP-запроса: %s", exc)
            result = {"status": "failed", "reason": str(exc)}
        return result


# ---------------------------------------------------------------------------
# EvoMetaCore orchestrator
# ---------------------------------------------------------------------------


class EvoMetaCore:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or DEFAULT_CONFIG
        self.log_dir = configure_logging(self.config)
        self.memory_manager = HierarchicalPyramidMemory(self.log_dir, self.config)
        self.container_orchestrator = ContainerOrchestrator(self)
        self.data_assimilation_nexus = DataAssimilationNexus(self)
        self.self_awareness_core = SelfAwarenessCore(self)
        self.emotional_palette = EmotionalPalette(self)
        self.cognitive_fusion_matrix = CognitiveFusionMatrix(self)
        self.hierarchical_goal_pyramid = HierarchicalGoalPyramid(self)
        self.creative_engine = CreativeEngine(self)
        self.role_evolution_engine = RoleEvolutionEngine(self)
        self.interface_adapter = InterfaceAdapter(self)
        self.ethics_core = EthicsCore(self)
        self.action_engine = ActionEngine(self)
        self.context_engine: Optional["EvoCodexContextEngine"] = self._init_context_engine()
        self.is_running = True
        logger.info("EvoMetaCore: инициализация завершена.")

    def _init_context_engine(self) -> Optional["EvoCodexContextEngine"]:
        """Attempt to initialise the optional Quantum Context Engine."""

        if get_context_engine is None:
            logger.warning("Quantum Context Engine недоступен: модуль не найден.")
            return None

        try:
            engine = get_context_engine()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Ошибка инициализации Quantum Context Engine: %s", exc)
            return None

        logger.info("Quantum Context Engine: инициализация успешна.")
        return engine

    @staticmethod
    def _run_async(coroutine: Coroutine[Any, Any, Any]) -> Any:
        """Run an async coroutine in a dedicated event loop."""

        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coroutine)
        finally:
            asyncio.set_event_loop(None)
            loop.close()

    def process_context_query(
        self, query: str, existing_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a natural-language query through the context engine."""

        if not self.context_engine:
            logger.warning(
                "Quantum Context Engine отключён, используется резервный ответ.")
            return {
                "success": False,
                "response": f"Context engine unavailable for query: {query}",
                "error": "context_engine_unavailable",
            }

        async def _execute() -> Dict[str, Any]:
            return await self.context_engine.process_query(query, existing_context)

        try:
            result = self._run_async(_execute())
        except Exception as exc:  # noqa: BLE001
            logger.exception("Context engine error: %s", exc)
            return {
                "success": False,
                "response": f"Context engine error: {exc}",
                "error": str(exc),
            }

        affect = (result.get("context") or {}).get("affect") or {}
        affect_intensity = float(affect.get("intensity", 0.5))
        tags = ["context_engine", result.get("priority_path", "unknown_path")]

        self.memory_manager.save_memory(
            {
                "query": query,
                "response": result.get("response"),
                "priority_path": result.get("priority_path"),
                "context": result.get("context"),
            },
            tags,
            "context_response",
            level=1,
            affective_score=affect_intensity,
        )

        return result

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        if task.get("use_context_engine") or task.get("type") == "context_query":
            query = str(task.get("data") or task.get("query") or "")
            existing_context = task.get("context") if isinstance(task.get("context"), dict) else None
            context_result = self.process_context_query(query, existing_context)
            status = "success" if context_result.get("success", False) else "failed"
            return {"status": status, "context_engine": context_result}

        if not self.ethics_core.check_action_ethics(task.get("type", "task"), task.get("data", "")):
            return {"status": "failed", "reason": "Этический конфликт"}

        sense_packet = self.data_assimilation_nexus.process_multimodal_input(
            task.get("data", ""),
            task.get("type", "text"),
        )
        insight = self.cognitive_fusion_matrix.fuse_data(sense_packet)
        self.hierarchical_goal_pyramid.add_goal(str(task.get("data", "Новая задача")), task.get("priority", 1))
        goal = self.hierarchical_goal_pyramid.select_next_goal()
        state = self.self_awareness_core.analyze_state()
        action_result = self.action_engine.execute_action(insight, goal)
        output = self.interface_adapter.render_output(insight, task.get("output_format", "text"))
        return {
            "status": "success",
            "insight": insight,
            "state": state,
            "action_result": action_result,
            "output": output,
        }

    def run(self) -> None:
        example_task = {
            "type": "image_analysis",
            "data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg==",
            "priority": 2,
            "output_format": "xml",
        }
        while self.is_running:
            result = self.container_orchestrator.distribute_task(example_task)
            logger.info("Результат: %s", result.get("output"))
            self.memory_manager.cleanup()
            time.sleep(5)

    def stop(self) -> None:
        self.is_running = False
        logger.info("EvoMetaCore: полёт завершён.")

    def joke(self) -> None:
        logger.info("Evo не запасует, он предсказывает квантовые иерархии! 😎")


# ---------------------------------------------------------------------------
# Flask application factory
# ---------------------------------------------------------------------------


def create_app(config_path: Optional[str] = None) -> Flask:
    config = load_config(config_path)
    core = EvoMetaCore(config)
    app = Flask(__name__)

    @app.route("/api/process_task", methods=["POST"])
    def process_task() -> Any:  # noqa: D401
        """Process an incoming task through the EvoMetaCore."""

        task = request.json or {}
        result = core.container_orchestrator.distribute_task(task)
        return jsonify(result)

    @app.route("/api/context_query", methods=["POST"])
    def context_query() -> Any:  # noqa: D401
        """Run a raw query through the Quantum Context Engine."""

        payload = request.json or {}
        query = str(payload.get("query", ""))
        existing_context = payload.get("context") if isinstance(payload.get("context"), dict) else None
        result = core.process_context_query(query, existing_context)
        return jsonify(result)

    @app.route("/api/get_pyramid", methods=["GET"])
    def get_pyramid() -> Any:  # noqa: D401
        """Return the current memory pyramid as XML."""

        return core.memory_manager.to_xml()

    app.evo_core = core  # type: ignore[attr-defined]
    return app


def run_app(config_path: Optional[str] = None) -> None:
    config = load_config(config_path)
    app = create_app(config_path)
    host = config["server"].get("host", DEFAULT_CONFIG["server"]["host"])
    port = int(config["server"].get("port", DEFAULT_CONFIG["server"]["port"]))
    debug = bool(config["server"].get("debug", DEFAULT_CONFIG["server"]["debug"]))
    use_reloader = bool(config["server"].get("use_reloader", DEFAULT_CONFIG["server"]["use_reloader"]))
    core: EvoMetaCore = app.evo_core  # type: ignore[attr-defined]
    core.joke()
    app.run(host=host, port=port, debug=debug, use_reloader=use_reloader)


if __name__ == "__main__":
    config_path = os.environ.get("EVO_CONFIG", os.path.join(os.path.dirname(__file__), "..", "..", "EvoMETA", "evo_config.yaml"))
    run_app(config_path)
