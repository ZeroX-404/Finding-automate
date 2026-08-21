from __future__ import annotations

from .state import (
    ResearchState,
    ConfidenceEngine,
    DecisionEngine,
)


def run_state_acceptance_case():

    state = ResearchState(
        hypothesis_id="HYP-state-demo"
    )

    state.add_supporting_evidence(4)

    confidence = ConfidenceEngine().calculate(state)

    decision = DecisionEngine().decide(state)

    return {
        "case": "research-state-v2.0",
        "hypothesis_id": state.hypothesis_id,
        "confidence": confidence,
        "decision": decision.value,
        "state": state.to_dict(),
        "audit": {
            "ok": True
        }
    }
