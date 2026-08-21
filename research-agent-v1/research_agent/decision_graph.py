from __future__ import annotations

from .models import EdgeRelation


def link_decision_to_state(
    ledger,
    decision_id: str,
    state_id: str,
):
    ledger.add_edge(
        decision_id,
        EdgeRelation.DECIDES_ON,
        state_id,
        metadata={
            "relation_type":
                "planner_decision_lineage"
        },
    )


def link_state_to_decision(
    ledger,
    state_id: str,
    decision_id: str,
):
    ledger.add_edge(
        state_id,
        EdgeRelation.PRODUCES,
        decision_id,
        metadata={
            "relation_type":
                "planner_output"
        },
    )
