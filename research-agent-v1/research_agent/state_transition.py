from __future__ import annotations

from .models import (
    Finding,
    ResearchState,
    Validation,
)

from .state_machine import transition_finding

from .state.decision import ResearchAction


class StateTransitionEngine:


    def __init__(
        self,
        ledger=None,
    ):
        self.ledger = ledger



    def apply(
        self,
        finding: Finding,
        action: ResearchAction,
        validations: list[Validation] | None = None,
    ) -> Finding:


        validations = validations or []


        if action == ResearchAction.PROMOTE_FINDING:

            new_state = ResearchState.CONFIRMED


        elif action == ResearchAction.DROP_HYPOTHESIS:

            new_state = ResearchState.REJECTED


        elif action == ResearchAction.REQUEST_MORE_EVIDENCE:

            new_state = ResearchState.UNDER_TEST


        else:

            return finding



        updated = transition_finding(
            finding,
            new_state,
            validations,
        )


        if self.ledger:

            self.ledger.put(
                updated
            )


        return updated
