from __future__ import annotations

class PlannerBinding:

    def __init__(self, decision_engine, orchestrator):
        self.decision_engine = decision_engine
        self.orchestrator = orchestrator

    def run(self, hypothesis_id: str, context: dict, critic_clean: bool = False):
        decision = self.decision_engine.evaluate(
            hypothesis_id,
            critic_clean=critic_clean,
        )

        return {
            "decision": decision,
            "context": context,
        }
