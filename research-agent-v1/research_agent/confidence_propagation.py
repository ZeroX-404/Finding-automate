from __future__ import annotations


class EvidenceConfidenceEngine:

    SUPPORT_WEIGHT = 0.15
    CONTRADICT_WEIGHT = 0.20


    def __init__(self, ledger):

        self.ledger = ledger


    def calculate(
        self,
        hypothesis_id: str,
        base_confidence: float = 0.5,
    ) -> dict:

        graph = self.ledger.export_graph()

        support = 0
        contradict = 0


        for edge in graph["edges"]:

            if edge["target_id"] != hypothesis_id:
                continue


            if edge["relation"] == "SUPPORTS":
                support += 1


            if edge["relation"] == "CONTRADICTS":
                contradict += 1


        score = (
            base_confidence
            + (support * self.SUPPORT_WEIGHT)
            - (contradict * self.CONTRADICT_WEIGHT)
        )


        score = max(
            0.0,
            min(
                1.0,
                score
            )
        )


        return {
            "hypothesis_id": hypothesis_id,
            "supporting_evidence": support,
            "contradicting_evidence": contradict,
            "confidence": score,
        }
