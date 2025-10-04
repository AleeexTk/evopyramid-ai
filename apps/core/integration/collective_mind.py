from __future__ import annotations
import asyncio, time
from typing import Dict, Any

from apps.core.intent.intent_classifier import IntentStreamClassifier
from apps.core.integration.context_engine import get_context_engine  # уже есть в репо
from apps.core.agi_proto.roles import run_role_panel
from apps.core.consensus.consensus_engine import ConsensusEngine
from apps.core.monitoring.flow_monitor import FlowMonitor

class CollectiveMindV1:
    """
    лёгкий оркестратор:
      1) Intent классификация
      2) Контекстный анализ (ContextEngine)
      3) Ролевое обсуждение (AGI-proто)
      4) Консенсус
      5) Лог метрик потока
    """
    def __init__(self):
        self.classifier = IntentStreamClassifier()
        self.ctx = get_context_engine()
        self.consensus = ConsensusEngine()
        self.flow = FlowMonitor()

    async def run(self, query: str) -> Dict[str, Any]:
        t0 = time.time()
        intent = self.classifier.classify(query)
        if intent.kind == "FLOOD":
            out = {
                "status":"filtered",
                "intent": intent.__dict__,
                "message": "Флуд выявлен — логируем отдельно, ядро не вовлекаем."
            }
            self.flow.log({
                "kind":"FLOOD","latency": time.time()-t0,"coherence":0.0,"novelty":0.0,
                "soul_resonance":0.0,"density":0.0
            })
            return out

        # 2) контекст
        ctx_result = await self.ctx.process_query(query)
        context = ctx_result.get("context", {})

        # 3) панель ролей
        proposals = [p.__dict__ for p in run_role_panel(query, context)]

        # 4) консенсус
        c = self.consensus.decide(proposals, context)

        # 5) метрики потока
        text_for_coh = ctx_result.get("response","")
        self.flow.log({
            "kind": intent.kind,
            "latency": time.time()-t0,
            "coherence": self.flow.compute_coherence(text_for_coh),
            "novelty": self.flow.compute_novelty(context),
            "soul_resonance": float(context.get("affect",{}).get("soul_resonance",0.0)),
            "density": c.details.get("density",0.0),
            "consensus_score": c.score,
            "consensus_decision": c.decision,
            "consensus_state": c.state
        })

        return {
            "status":"ok",
            "intent": intent.__dict__,
            "priority_path": ctx_result.get("priority_path"),
            "context_affect": context.get("affect", {}),
            "role_proposals": proposals,
            "consensus": c.__dict__,
            "response": ctx_result.get("response","")
        }

if __name__ == "__main__":
    async def demo():
        cm = CollectiveMindV1()
        for q in [
            "Разработай архитектуру модуля интеграции AGI в EvoPyramid",
            "Как коллективный разум меняет сознание?",
            "Привет как дела"
        ]:
            r = await cm.run(q)
            print("\n===", q, "===\n", r["status"], "| intent:", r["intent"]["kind"], "| decision:", r.get("consensus",{}).get("decision"))
    asyncio.run(demo())

