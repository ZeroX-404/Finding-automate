from __future__ import annotations

from dataclasses import dataclass, field



@dataclass
class GovernanceDecision:

    allowed: bool

    risk_score: float

    reason: str



class AgentGovernanceEngine:


    def __init__(self):

        self.blocked_actions = {
            "DELETE_DATA",
            "ALTER_LEDGER",
        }


        self.high_risk_actions = {
            "EXECUTE_CODE",
            "MODIFY_SOURCE",
        }



    def evaluate(
        self,
        agent: str,
        action: str,
    ):

        if action in self.blocked_actions:

            return GovernanceDecision(
                allowed=False,
                risk_score=1.0,
                reason="blocked_action",
            )


        if action in self.high_risk_actions:

            return GovernanceDecision(
                allowed=False,
                risk_score=0.8,
                reason="requires_approval",
            )


        return GovernanceDecision(
            allowed=True,
            risk_score=0.1,
            reason="policy_allowed",
        )



    def can_execute(
        self,
        agent: str,
        action: str,
    ):

        result = self.evaluate(
            agent,
            action,
        )

        return result.allowed
