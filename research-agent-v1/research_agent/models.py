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


class Observation(BaseModel):
    id: str = Field(default_factory=lambda: new_id("OBS"))
    summary: str
    artifact: str | None = None
    location: str | None = None
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


class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: new_id("EVD"))
    description: str
    source_type: str
    source_ref: str
    relation: EvidenceRelation
    immutable_hash: str | None = None
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
    evidence_ids: list[str] = Field(default_factory=list)
    validation_ids: list[str] = Field(default_factory=list)
    cwe: str | None = None
    cve: str | None = None
    cvss_vector: str | None = None
    provenance: Provenance
