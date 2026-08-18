from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

from .ledger import Ledger, sha256_file, sha256_text
from .models import (
    Claim,
    ClaimState,
    CriticRecord,
    CriticVerdict,
    EdgeRelation,
    Evidence,
    EvidenceRelation,
    Experiment,
    ExperimentStatus,
    Finding,
    Hypothesis,
    Method,
    MethodKind,
    Observation,
    Provenance,
    ResearchState,
    Source,
    SourceType,
    Validation,
    ValidationLevel,
)
from .state_machine import transition_finding


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _fixture_path() -> Path:
    return _project_root() / "examples" / "synthetic_target" / "access_control.py"


def _load_fixture(path: Path):
    spec = importlib.util.spec_from_file_location("research_agent_synthetic_target", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load synthetic target: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prov(actor: str, *, tool_name: str | None = None, parent_ids: list[str] | None = None) -> Provenance:
    return Provenance(
        created_by=actor,
        tool_name=tool_name,
        scope_id="local-security-research-v1",
        parent_ids=parent_ids or [],
    )


def run_synthetic_case(ledger: Ledger) -> dict[str, Any]:
    """Create one complete, local-only security research lineage in the ledger.

    This is an acceptance harness for the evidence architecture. It performs no
    network access and targets only the repository-owned synthetic fixture.
    """
    ledger.init()
    fixture = _fixture_path()
    if not fixture.exists():
        raise FileNotFoundError(f"Synthetic target is missing: {fixture}")

    source = Source(
        source_type=SourceType.FILE,
        reference=str(fixture.relative_to(_project_root())),
        content_hash=sha256_file(fixture),
        metadata={"purpose": "V1 acceptance fixture", "authorized": True},
        provenance=_prov("synthetic-harness", tool_name="filesystem"),
    )

    method = Method(
        name="local deterministic authorization reproduction",
        kind=MethodKind.REPRODUCTION,
        version="1",
        deterministic=True,
        parameters={"network": False, "target": "repository-owned synthetic fixture"},
        provenance=_prov("synthetic-harness", tool_name="python"),
    )

    observation = Observation(
        summary="read_profile indexes profiles by requested_user without an ownership check in the function body.",
        artifact=source.reference,
        location=f"{source.reference}:5-7",
        source_id=source.id,
        method_id=method.id,
        raw={"symbol": "read_profile", "authorization_check_observed": False},
        provenance=_prov(
            "synthetic-researcher",
            tool_name="manual-static-review",
            parent_ids=[source.id, method.id],
        ),
    )

    hypothesis = Hypothesis(
        statement="read_profile permits a caller to retrieve another user's profile when requested_user differs from current_user.",
        falsifier="The function rejects a cross-user request or returns no data when current_user != requested_user.",
        prediction="Calling read_profile('alice', 'bob', profiles) returns Bob's profile.",
        observation_ids=[observation.id],
        model_confidence=None,
        provenance=_prov("synthetic-researcher", parent_ids=[observation.id]),
    )

    profiles = {"alice": "alice-private", "bob": "bob-private"}
    module = _load_fixture(fixture)
    attempts: list[dict[str, Any]] = []
    for attempt in range(1, 4):
        result = module.read_profile("alice", "bob", profiles)
        attempts.append(
            {
                "attempt": attempt,
                "requester": "alice",
                "requested_user": "bob",
                "observed": result,
                "cross_user_read": result == profiles["bob"],
            }
        )

    passes = sum(1 for attempt in attempts if attempt["cross_user_read"])
    observed_result = json.dumps(attempts, sort_keys=True)

    experiment = Experiment(
        hypothesis_id=hypothesis.id,
        method_id=method.id,
        objective="Test whether the local fixture enforces object ownership inside read_profile.",
        procedure=[
            "Load the repository-owned synthetic fixture locally.",
            "Create profiles for Alice and Bob.",
            "Call read_profile as Alice while requesting Bob.",
            "Repeat three times and record whether Bob's value is returned.",
        ],
        expected_result="If authorization is enforced, Alice must not receive Bob's profile.",
        observed_result=observed_result,
        status=ExperimentStatus.COMPLETED,
        provenance=_prov(
            "synthetic-harness",
            tool_name="python",
            parent_ids=[hypothesis.id, method.id],
        ),
    )

    evidence = Evidence(
        description=f"Cross-user profile retrieval reproduced {passes}/3 times in the local fixture.",
        source_type=SourceType.FILE.value,
        source_ref=source.reference,
        relation=EvidenceRelation.SUPPORTS,
        source_id=source.id,
        method_id=method.id,
        experiment_id=experiment.id,
        immutable_hash=sha256_text(observed_result),
        provenance=_prov(
            "synthetic-harness",
            tool_name="python",
            parent_ids=[source.id, experiment.id],
        ),
    )

    claim = Claim(
        statement="The read_profile function itself does not enforce object-level ownership and directly returns a different user's profile.",
        state=ClaimState.SUPPORTED if passes == 3 else ClaimState.INCONCLUSIVE,
        hypothesis_id=hypothesis.id,
        provenance=_prov(
            "synthetic-researcher",
            parent_ids=[hypothesis.id, evidence.id],
        ),
    )

    critic = CriticRecord(
        subject_id=claim.id,
        verdict=CriticVerdict.SUPPORTS if passes == 3 else CriticVerdict.INCONCLUSIVE,
        objections=[],
        missing_evidence=[
            "No application-level caller graph is represented; the conclusion is intentionally limited to function-level authorization enforcement."
        ],
        alternative_explanations=[
            "A real application could enforce authorization before calling this function; that broader context is outside this synthetic fixture."
        ],
        provenance=_prov(
            "synthetic-critic",
            tool_name="rule-based-critic",
            parent_ids=[claim.id, evidence.id],
        ),
    )

    finding = Finding(
        title="Synthetic object-level authorization defect",
        description=(
            "Repository-owned acceptance fixture: read_profile accepts current_user but does not use it to enforce ownership. "
            "The finding is scoped to the function itself and does not claim application-wide exploitability."
        ),
        state=ResearchState.UNDER_TEST,
        hypothesis_id=hypothesis.id,
        claim_ids=[claim.id],
        evidence_ids=[evidence.id],
        critic_ids=[critic.id],
        cwe="CWE-639",
        provenance=_prov(
            "synthetic-researcher",
            parent_ids=[claim.id, evidence.id, critic.id],
        ),
    )

    critic_validation = Validation(
        subject_id=finding.id,
        level=ValidationLevel.V1_CRITIC,
        passed=critic.verdict == CriticVerdict.SUPPORTS,
        rationale="Critic accepted the narrow function-level claim while explicitly constraining broader application impact.",
        provenance=_prov(
            "synthetic-validator",
            tool_name="rule-based-critic-gate",
            parent_ids=[critic.id, finding.id],
        ),
    )

    deterministic_validation = Validation(
        subject_id=finding.id,
        level=ValidationLevel.V3_DETERMINISTIC,
        passed=passes == 3,
        rationale=f"Cross-user retrieval reproduced {passes}/3 times with identical local inputs.",
        reproducibility_passes=passes,
        reproducibility_attempts=3,
        provenance=_prov(
            "synthetic-validator",
            tool_name="python",
            parent_ids=[experiment.id, evidence.id, finding.id],
        ),
    )

    objects = (
        source,
        method,
        observation,
        hypothesis,
        experiment,
        evidence,
        claim,
        critic,
        finding,
        critic_validation,
        deterministic_validation,
    )
    for obj in objects:
        ledger.put(obj)

    edges = (
        (observation.id, EdgeRelation.OBSERVED_FROM, source.id),
        (observation.id, EdgeRelation.USES_METHOD, method.id),
        (hypothesis.id, EdgeRelation.MOTIVATED_BY, observation.id),
        (experiment.id, EdgeRelation.TESTS, hypothesis.id),
        (experiment.id, EdgeRelation.USES_METHOD, method.id),
        (experiment.id, EdgeRelation.PRODUCES, evidence.id),
        (evidence.id, EdgeRelation.OBSERVED_FROM, source.id),
        (evidence.id, EdgeRelation.SUPPORTS, claim.id),
        (claim.id, EdgeRelation.DERIVED_FROM, hypothesis.id),
        (critic.id, EdgeRelation.CRITICIZES, claim.id),
        (finding.id, EdgeRelation.DERIVED_FROM, claim.id),
        (critic.id, EdgeRelation.CRITICIZES, finding.id),
        (critic_validation.id, EdgeRelation.VALIDATES, finding.id),
        (deterministic_validation.id, EdgeRelation.VALIDATES, finding.id),
    )
    for source_id, relation, target_id in edges:
        ledger.add_edge(source_id, relation, target_id)

    confirmed = transition_finding(
        finding,
        ResearchState.CONFIRMED,
        [critic_validation, deterministic_validation],
    )
    ledger.put(confirmed)

    audit = ledger.audit()
    if not audit["ok"]:
        raise RuntimeError(f"Synthetic case produced an invalid ledger: {audit['issues']}")

    return {
        "finding_id": confirmed.id,
        "state": confirmed.state.value,
        "source_id": source.id,
        "hypothesis_id": hypothesis.id,
        "experiment_id": experiment.id,
        "evidence_id": evidence.id,
        "claim_id": claim.id,
        "critic_id": critic.id,
        "critic_validation_id": critic_validation.id,
        "deterministic_validation_id": deterministic_validation.id,
        "reproducibility": {"passes": passes, "attempts": 3},
        "audit": audit,
    }
