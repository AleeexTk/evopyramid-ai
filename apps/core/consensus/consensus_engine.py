from __future__ import annotations
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ConsensusResult:
    score: float
    decision: str     # evolve | approve | modify | reject
    state: str        # platinum | gold | standard
    summary: str
    details: Dict[str, Any]

class ConsensusEngine:
    def __init__(self, threshold_gold=0.7, threshold_platinum=0.9):
        self.tg = threshold_gold
        self.tp = threshold_platinum

    def decide(self, proposals: List[Dict[str, Any]], context: Dict[str, Any]) -> ConsensusResult:
        if not proposals:
            return ConsensusResult(0.0,"reject","standard","нет предложений",{"proposals":[]})

        approves = sum(1 for p in proposals if p["stance"]=="approve")
        total_w  = sum(p.get("weight",0.7) for p in proposals)
        emotion_boost = 0.0
        affect = context.get("affect", {})
        if affect:
            # лёгкий буст при высокой интенсивности
            emotion_boost = float(affect.get("intensity", 0.0))*0.1

        score = (approves/len(proposals))*total_w/len(proposals) + emotion_boost

        # density как простая функция контента
        content = (context.get("intent",{}).get("type","") + str(context.get("memory",{}))).lower()
        density = min(1.5, max(0.0, len(content)/250.0))

        if score>=self.tp and density>1.2:
            decision, state = "evolve","platinum"
        elif score>=self.tg and density>0.8:
            decision, state = "approve","gold"
        else:
            decision, state = ("modify" if score>=0.5 else "reject"), "standard"

        summary = f"score={score:.2f}, density={density:.2f}, approves={approves}/{len(proposals)}"
        return ConsensusResult(score, decision, state, summary, {"proposals":proposals,"density":density})

