from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


class ResearchState(StrEnum):
    OBSERVATION = "OBSERVATION"
    CANDIDATE = "CANDIDATE"
    HYPOTHESIS = "HYPOTHESIS"
    UNDER_TEST = "UNDER_TEST"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    DUPLICATE = "DUPLICATE"


class ValidationLevel(StrEnum):
    V0_SELF_CHECK = "V0_SELF_CHECK"
    V1_CRITIC = "V1_CRITIC"
    V2_TOOL_CORROBORATION = "V2_TOOL_CORROBORATION"
    V3_DETERMINISTIC = "V3_DETERMINISTIC"
    V4_HUMAN = "V4_HUMAN"


class EvidenceRelation(StrEnum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    NEUTRAL = "NEUTRAL"


class EdgeRelation(StrEnum):
    DERIVED_FROM = "DERIVED_FROM"
    OBSERVED_FROM = "OBSERVED_FROM"
    MOTIVATED_BY = "MOTIVATED_BY"
    TESTS = "TESTS"
    USES_METHOD = "USES_METHOD"
    PRODUCES = "PRODUCES"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    CRITICIZES = "CRITICIZES"
    VALIDATES = "VALIDATES"
    REFERENCES = "REFERENCES"
    REMEDIATES = "REMEDIATES"
    BEARS_ON = "BEARS_ON"
    ASSESSES = "ASSESSES"
    PROPOSES_FOR = "PROPOSES_FOR"
    DECIDES_ON = "DECIDES_ON"
    PROMOTES_TO = "PROMOTES_TO"
    ROUTES_TO = "ROUTES_TO"


class SourceType(StrEnum):
    REPOSITORY = "REPOSITORY"
    FILE = "FILE"
    TOOL_OUTPUT = "TOOL_OUTPUT"
    DATASET = "DATASET"
    DOCUMENT = "DOCUMENT"
    MANUAL = "MANUAL"


class MethodKind(StrEnum):
    STATIC_ANALYSIS = "STATIC_ANALYSIS"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REPRODUCTION = "REPRODUCTION"
    PARSER = "PARSER"
    MODEL_REASONING = "MODEL_REASONING"
    TEST = "TEST"
    CRITIC_REVIEW = "CRITIC_REVIEW"
    PROPOSAL_GATE = "PROPOSAL_GATE"
    EVIDENCE_EXECUTOR = "EVIDENCE_EXECUTOR"


class ExperimentStatus(StrEnum):
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ClaimState(StrEnum):
    CANDIDATE = "CANDIDATE"
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class AssessmentStatus(StrEnum):
    SUSPICIOUS = "SUSPICIOUS"
    WEAKENED = "WEAKENED"
    INCONCLUSIVE = "INCONCLUSIVE"
    NO_MATCH = "NO_MATCH"


class CriticVerdict(StrEnum):
    SUPPORTS = "SUPPORTS"
    CHALLENGES = "CHALLENGES"
    REJECTS = "REJECTS"
    INCONCLUSIVE = "INCONCLUSIVE"


class ProposalKind(StrEnum):
    HYPOTHESIS_REFINEMENT = "HYPOTHESIS_REFINEMENT"
    EVIDENCE_REQUEST = "EVIDENCE_REQUEST"


class ProposalDisposition(StrEnum):
    CONTINUE = "CONTINUE"
    SEEK_EVIDENCE = "SEEK_EVIDENCE"
    DEPRIORITIZE = "DEPRIORITIZE"


class ProposalStatus(StrEnum):
    PROPOSED = "PROPOSED"
    REJECTED = "REJECTED"
    ACCEPTED = "ACCEPTED"


class PromotionDecision(StrEnum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    DEFER = "DEFER"

class OrchestratorStatus(StrEnum):
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Provenance(BaseModel):
    created_by: str
    model_id: str | None = None
    tool_name: str | None = None
    tool_version: str | None = None
    repo_commit: str | None = None
    input_hash: str | None = None
    output_hash: str | None = None
    scope_id: str | None = None
    parent_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class Source(BaseModel):
    id: str = Field(default_factory=lambda: new_id("SRC"))
    source_type: SourceType
    reference: str
    content_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: Provenance


class Method(BaseModel):
    id: str = Field(default_factory=lambda: new_id("MTH"))
    name: str
    kind: MethodKind
    version: str | None = None
    deterministic: bool = False
    parameters: dict[str, Any] = Field(default_factory=dict)
    provenance: Provenance


class Observation(BaseModel):
    id: str = Field(default_factory=lambda: new_id("OBS"))
    summary: str
    artifact: str | None = None
    location: str | None = None
    source_id: str | None = None
    method_id: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)
    provenance: Provenance


class Hypothesis(BaseModel):
    id: str = Field(default_factory=lambda: new_id("HYP"))
    statement: str
    falsifier: str
    prediction: str
    state: ResearchState = ResearchState.HYPOTHESIS
    observation_ids: list[str] = Field(default_factory=list)
    model_confidence: float | None = Field(default=None, ge=0, le=1)
    provenance: Provenance


class Experiment(BaseModel):
    id: str = Field(default_factory=lambda: new_id("EXP"))
    hypothesis_id: str
    method_id: str
    objective: str
    procedure: list[str] = Field(default_factory=list)
    expected_result: str
    observed_result: str | None = None
    status: ExperimentStatus = ExperimentStatus.PLANNED
    provenance: Provenance


class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: new_id("EVD"))
    description: str
    source_type: str
    source_ref: str
    relation: EvidenceRelation
    source_id: str | None = None
    method_id: str | None = None
    experiment_id: str | None = None
    immutable_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: Provenance


class ContextAssessment(BaseModel):
    id: str = Field(default_factory=lambda: new_id("CAS"))
    hypothesis_id: str
    status: AssessmentStatus
    rationale: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradictory_evidence_ids: list[str] = Field(default_factory=list)
    neutral_evidence_ids: list[str] = Field(default_factory=list)
    provenance: Provenance


class Claim(BaseModel):
    id: str = Field(default_factory=lambda: new_id("CLM"))
    statement: str
    state: ClaimState = ClaimState.CANDIDATE
    hypothesis_id: str | None = None
    provenance: Provenance


class CriticRecord(BaseModel):
    id: str = Field(default_factory=lambda: new_id("CRT"))
    subject_id: str
    verdict: CriticVerdict
    assessment_id: str | None = None
    method_id: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    alternative_explanations: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    provenance: Provenance


class ResearchProposal(BaseModel):
    id: str = Field(default_factory=lambda: new_id("PRP"))
    subject_id: str
    assessment_id: str
    critic_id: str
    method_id: str
    proposal_kind: ProposalKind
    disposition: ProposalDisposition
    status: ProposalStatus = ProposalStatus.PROPOSED
    statement: str
    falsifier: str
    prediction: str
    requested_evidence: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    model_output_hash: str
    repository_content_treated_as_data: bool = True
    schema_version: str = "1"
    provenance: Provenance


class ProposalDecision(BaseModel):
    id: str = Field(default_factory=lambda: new_id("PGD"))
    proposal_id: str
    subject_id: str
    method_id: str
    decision: PromotionDecision
    rationale: str
    reason_codes: list[str] = Field(default_factory=list)
    promoted_hypothesis_id: str | None = None
    deterministic: bool = True
    gate_version: str = "1.7"
    provenance: Provenance


class Validation(BaseModel):
    id: str = Field(default_factory=lambda: new_id("VAL"))
    subject_id: str
    level: ValidationLevel
    passed: bool
    rationale: str
    reproducibility_passes: int = 0
    reproducibility_attempts: int = 0
    provenance: Provenance


class Finding(BaseModel):
    id: str = Field(default_factory=lambda: new_id("FIND"))
    title: str
    description: str
    state: ResearchState = ResearchState.CANDIDATE
    hypothesis_id: str | None = None
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    validation_ids: list[str] = Field(default_factory=list)
    critic_ids: list[str] = Field(default_factory=list)
    cwe: str | None = None
    cve: str | None = None
    cvss_vector: str | None = None
    provenance: Provenance




class OrchestratorEvent(BaseModel):
    id: str = Field(
        default_factory=lambda: new_id("ORCH")
    )

    decision_id: str

    agent_name: str

    status: OrchestratorStatus

    input_payload: dict[str, Any] = Field(
        default_factory=dict
    )

    output_payload: dict[str, Any] = Field(
        default_factory=dict
    )

    error: str | None = None

    orchestrator_version: str = "2.2.2"

    provenance: Provenance




class AgentSelectionEvent(BaseModel):
    id: str = Field(
        default_factory=lambda: new_id("ASE")
    )

    decision_id: str

    action: str

    selected_agent: str

    provenance: Provenance
