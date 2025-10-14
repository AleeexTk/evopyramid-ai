from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List
import time

@dataclass
class RoleProposal:
    role: str
    stance: str          # "approve" | "modify" | "reject"
    rationale: str
    weight: float        # базовый вес роли
    payload: Dict[str, Any]

class BaseRole:
    name = "Base"
    base_weight = 0.7
    def propose(self, query: str, context: Dict[str, Any]) -> RoleProposal:
        return RoleProposal(self.name, "modify", "Base noop", self.base_weight, {"echo": query})

class Absolut(BaseRole):
    name = "Absolut"
    base_weight = 0.95
    def propose(self, query: str, context: Dict[str, Any]) -> RoleProposal:
        rationale = "Структурирую задачу и свожу к исполнимому плану."
        stance = "approve" if "архитектура" in query.lower() or "код" in query.lower() else "modify"
        payload = {
            "plan": [
                "Уточнить целевой модуль/поверхность",
                "Определить вход/выход",
                "Собрать минимальный пруф",
            ],
            "timestamp": time.time(),
        }
        return RoleProposal(self.name, stance, rationale, self.base_weight, payload)

class Archivarius(BaseRole):
    name = "Archivarius"
    base_weight = 0.88
    def propose(self, query: str, context: Dict[str, Any]) -> RoleProposal:
        mem = context.get("memory", {})
        hits = mem.get("fragments", []) if isinstance(mem, dict) else []
        rationale = f"Сопоставляю с {len(hits)} фрагментами памяти для консистентности."
        stance = "approve" if hits else "modify"
        payload = {"references": hits[:5]}
        return RoleProposal(self.name, stance, rationale, self.base_weight, payload)

class Evochka(BaseRole):
    name = "Evochka"
    base_weight = 0.9
    def propose(self, query: str, context: Dict[str, Any]) -> RoleProposal:
        affect = context.get("affect", {})
        emo = affect.get("emotion", "curiosity")
        rationale = f"Привношу креатив через эмоцию: {emo}."
        stance = "modify"
        payload = {"creative_hint": f"Вариант через {emo}-тон и образ."}
        return RoleProposal(self.name, stance, rationale, self.base_weight, payload)

def run_role_panel(query: str, context: Dict[str, Any]) -> List[RoleProposal]:
    roles = [Absolut(), Archivarius(), Evochka()]
    return [r.propose(query, context) for r in roles]

