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


def validation(finding, level, passed=True):
    return Validation(
        subject_id=finding.id,
        level=level,
        passed=passed,
        rationale="test validation",
        provenance=provenance(),
    )


def test_confirmation_requires_evidence():
    finding = Finding(
        title="Candidate",
        description="test",
        state=ResearchState.UNDER_TEST,
        provenance=provenance(),
    )
    critic = validation(finding, ValidationLevel.V1_CRITIC)
    deterministic = validation(finding, ValidationLevel.V3_DETERMINISTIC)

    with pytest.raises(ValueError, match="without evidence"):
        transition_finding(
            finding, ResearchState.CONFIRMED, [critic, deterministic]
        )


def test_confirmation_requires_critic():
    finding = Finding(
        title="Candidate",
        description="test",
        state=ResearchState.UNDER_TEST,
        evidence_ids=["EVD-test"],
        provenance=provenance(),
    )
    deterministic = validation(finding, ValidationLevel.V3_DETERMINISTIC)

    with pytest.raises(ValueError, match="critic"):
        transition_finding(finding, ResearchState.CONFIRMED, [deterministic])


def test_confirmation_requires_deterministic_validation():
    finding = Finding(
        title="Candidate",
        description="test",
        state=ResearchState.UNDER_TEST,
        evidence_ids=["EVD-test"],
        provenance=provenance(),
    )
    critic = validation(finding, ValidationLevel.V1_CRITIC)

    with pytest.raises(ValueError, match="deterministic"):
        transition_finding(finding, ResearchState.CONFIRMED, [critic])


def test_confirmation_with_required_gates():
    finding = Finding(
        title="Candidate",
        description="test",
        state=ResearchState.UNDER_TEST,
        evidence_ids=["EVD-test"],
        provenance=provenance(),
    )
    critic = validation(finding, ValidationLevel.V1_CRITIC)
    deterministic = validation(finding, ValidationLevel.V3_DETERMINISTIC)

    updated = transition_finding(
        finding, ResearchState.CONFIRMED, [critic, deterministic]
    )
    assert updated.state == ResearchState.CONFIRMED
    assert critic.id in updated.validation_ids
    assert deterministic.id in updated.validation_ids
