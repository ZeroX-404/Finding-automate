from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgentVote:

    agent: str

    decision: str

    confidence: float



class AgentConsensusEngine:


    def __init__(
        self,
        threshold: float = 0.75,
    ):

        self.threshold = threshold



    def evaluate(
        self,
        votes: list[AgentVote],
    ):

        if not votes:

            return {
                "decision": "NO_CONSENSUS",
                "score": 0,
            }


        scores = {}


        for vote in votes:

            weight = vote.confidence

            scores[vote.decision] = (
                scores.get(
                    vote.decision,
                    0,
                )
                +
                weight
            )


        winner = max(
            scores,
            key=scores.get,
        )


        total = sum(
            scores.values()
        )


        score = (
            scores[winner]
            /
            total
        )


        if score >= self.threshold:

            status = "ACCEPT"

        else:

            status = "REVIEW"


        return {
            "decision": winner,
            "score": score,
            "status": status,
            "votes": len(votes),
        }
