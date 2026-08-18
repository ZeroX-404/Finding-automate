import pytest

from research_agent.models import (
    Finding,
    Provenance,
    ResearchState,
    Validation,
    ValidationLevel,
)
from research_agent.state_machine import transition_finding


def provenance():
    return Provenance(created_by="test")


def test_confirmation_requires_deterministic_validation():
    finding = Finding(
        title="Candidate",
        description="test",
        state=ResearchState.UNDER_TEST,
        provenance=provenance(),
    )

    critic = Validation(
        subject_id=finding.id,
        level=ValidationLevel.V1_CRITIC,
        passed=True,
        rationale="looks supported",
        provenance=provenance(),
    )

    with pytest.raises(ValueError):
        transition_finding(finding, ResearchState.CONFIRMED, [critic])


def test_confirmation_with_v3_pass():
    finding = Finding(
        title="Candidate",
        description="test",
        state=ResearchState.UNDER_TEST,
        provenance=provenance(),
    )

    deterministic = Validation(
        subject_id=finding.id,
        level=ValidationLevel.V3_DETERMINISTIC,
        passed=True,
        rationale="deterministically reproduced",
        reproducibility_passes=3,
        reproducibility_attempts=3,
        provenance=provenance(),
    )

    updated = transition_finding(
        finding, ResearchState.CONFIRMED, [deterministic]
    )
    assert updated.state == ResearchState.CONFIRMED
