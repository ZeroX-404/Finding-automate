from __future__ import annotations

from dataclasses import dataclass



@dataclass
class EvidenceSignal:

    evidence_id: str

    relation: str

    strength: float = 0.5



class EvidenceReasoner:


    def __init__(self):

        self.signals = []



    def add_evidence(
        self,
        evidence_id: str,
        relation: str,
        strength: float = 0.5,
    ):

        signal = EvidenceSignal(
            evidence_id=evidence_id,
            relation=relation,
            strength=strength,
        )

        self.signals.append(
            signal
        )

        return signal



    def evaluate(self):

        support = 0.0

        contradict = 0.0


        for signal in self.signals:

            if signal.relation == "SUPPORTS":

                support += (
                    signal.strength
                )


            elif signal.relation == "CONTRADICTS":

                contradict += (
                    signal.strength
                )


        total = (
            support
            +
            contradict
        )


        if total == 0:

            confidence = 0.0

        else:

            confidence = (
                support
                /
                total
            )


        return {

            "support_score":
                support,

            "contradiction_score":
                contradict,

            "confidence":
                round(
                    confidence,
                    4,
                ),

            "evidence_count":
                len(self.signals),
        }
