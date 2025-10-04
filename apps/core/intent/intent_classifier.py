from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Dict, Any
import re

IntentKind = Literal["FLOOD","TECHNICAL","PHILOSOPHICAL","CREATIVE","META","OTHER"]

_KW_TECH = {"архитектура","api","код","python","llm","интеграция","test","pytest","pip","модуль","агент"}
_KW_PHIL = {"смысл","сознание","дух","meta","философия","путь","этика"}
_KW_CREAT = {"история","метафора","образ","поэзия","креатив","дизайн"}
_KW_META  = {"процесс","ритуал","гайд","документация","README","roadmap","адр","adr"}
_FLOOD_PAT = re.compile(r"^(привет|как дела|шо там|что нового)[!?.\s]*$", re.I)

@dataclass
class IntentSignal:
    kind: IntentKind
    confidence: float
    reason: str
    features: Dict[str, Any]

class IntentStreamClassifier:
    """
    Лёгкий эвристический классификатор намерения.
    Используется как pre-processor перед ContextEngine/DataFusion.
    """
    def classify(self, text: str) -> IntentSignal:
        t = (text or "").strip().lower()
        if not t:
            return IntentSignal("OTHER", 0.3, "empty", {})

        if _FLOOD_PAT.match(t) or len(t) < 8:
            return IntentSignal("FLOOD", 0.9, "smalltalk/short", {"len": len(t)})

        tokens = set(re.findall(r"[a-zа-я0-9_]+", t))
        score = {
            "TECHNICAL": len(tokens & _KW_TECH),
            "PHILOSOPHICAL": len(tokens & _KW_PHIL),
            "CREATIVE": len(tokens & _KW_CREAT),
            "META": len(tokens & _KW_META),
        }
        kind = max(score, key=score.get)
        if score[kind] == 0:
            return IntentSignal("OTHER", 0.5, "no strong cues", {"score": score})

        conf = min(0.6 + 0.1*score[kind], 0.95)
        return IntentSignal(kind, conf, f"keywords:{score[kind]}", {"score": score, "len": len(t)})

