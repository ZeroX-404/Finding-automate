from __future__ import annotations

from .state_persistence import snapshot_from_state
from .models import EdgeRelation


class StateMutationEngine:

    def __init__(
        self,
        ledger=None,
    ):
        self.ledger = ledger


    def apply_result(
        self,
        state,
        result,
        parent_ids=None,
    ):

        output = result.output or {}


        if "confidence" in output:
            state.confidence = float(
                output["confidence"]
            )


        if "next_action" in output:
            state.next_action = output[
                "next_action"
            ]


        evidence = output.get(
            "evidence",
            {}
        )


        if evidence.get("supporting"):
            state.add_supporting_evidence(
                evidence["supporting"]
            )


        if evidence.get("contradicting"):
            state.add_contradicting_evidence(
                evidence["contradicting"]
            )


        if evidence.get("neutral"):
            state.add_neutral_evidence(
                evidence["neutral"]
            )


        snapshot = snapshot_from_state(
            state
        )


        if self.ledger:

            self.ledger.put(
                snapshot
            )


            for parent in parent_ids or []:

                self.ledger.add_edge(
                    snapshot.id,
                    EdgeRelation.DERIVED_FROM,
                    parent,
                )


        return snapshot
