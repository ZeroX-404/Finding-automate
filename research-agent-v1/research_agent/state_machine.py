from __future__ import annotations

from .models import Finding, ResearchState, Validation, ValidationLevel


_ALLOWED = {
    ResearchState.CANDIDATE: {ResearchState.UNDER_TEST, ResearchState.REJECTED, ResearchState.DUPLICATE},
    ResearchState.UNDER_TEST: {
        ResearchState.CONFIRMED,
        ResearchState.REJECTED,
        ResearchState.INCONCLUSIVE,
    },
    ResearchState.CONFIRMED: set(),
    ResearchState.REJECTED: set(),
    ResearchState.INCONCLUSIVE: {ResearchState.UNDER_TEST},
    ResearchState.DUPLICATE: set(),
}


def transition_finding(finding: Finding, new_state: ResearchState, validations: list[Validation]) -> Finding:
    current = finding.state
    if new_state not in _ALLOWED.get(current, set()):
        raise ValueError(f"Illegal transition: {current} -> {new_state}")

    if new_state == ResearchState.CONFIRMED:
        deterministic_pass = any(
            v.level == ValidationLevel.V3_DETERMINISTIC and v.passed
            for v in validations
        )
        if not deterministic_pass:
            raise ValueError(
                "Finding cannot be CONFIRMED without a passing V3 deterministic validation."
            )

    return finding.model_copy(update={"state": new_state})
