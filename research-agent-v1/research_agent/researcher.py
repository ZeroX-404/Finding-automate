from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .ledger import Ledger, sha256_file, sha256_text
from .models import (
    EdgeRelation,
    Method,
    MethodKind,
    ProposalDisposition,
    ProposalKind,
    Provenance,
    ResearchProposal,
)
from .policy import Capability, ScopePolicy
from .research_models import ModelProposalOutput, ResearchModel, ResearchPacket
from .signal_pipeline import collect_source_context, resolve_repo_artifact


class ResearcherError(RuntimeError):
    pass


def _required(ledger: Ledger, object_id: str, kind: str) -> dict[str, Any]:
    obj = ledger.get(object_id)
    if obj is None:
        raise ResearcherError(f"unknown object: {object_id}")
    if obj["kind"] != kind:
        raise ResearcherError(f"{object_id} is {obj['kind']}, expected {kind}")
    return obj["payload"]


def _evidence_summaries(ledger: Ledger, assessment: dict[str, Any]) -> list[dict[str, Any]]:
    ids = list(dict.fromkeys(
        (assessment.get("supporting_evidence_ids") or [])
        + (assessment.get("contradictory_evidence_ids") or [])
        + (assessment.get("neutral_evidence_ids") or [])
    ))
    summaries: list[dict[str, Any]] = []
    for evidence_id in ids:
        evidence = _required(ledger, evidence_id, "Evidence")
        summaries.append(
            {
                "evidence_id": evidence_id,
                "relation": evidence.get("relation"),
                "description": evidence.get("description"),
                "source_ref": evidence.get("source_ref"),
                "fact_type": (evidence.get("metadata") or {}).get("fact_type"),
                "metadata": evidence.get("metadata") or {},
            }
        )
    return summaries


def build_research_packet(
    ledger: Ledger,
    assessment_id: str,
    critic_id: str,
    repo_root: str | Path,
    *,
    policy: ScopePolicy,
    context_radius: int = 4,
) -> ResearchPacket:
    """Build a structured model packet with an explicit trust boundary.

    Repository text may be included only inside ``untrusted_repository_data``.
    It never changes the trusted contract or tool permissions.
    """
    policy.require(Capability.REPO_READ)
    root = policy.require_repository(repo_root)

    assessment = _required(ledger, assessment_id, "ContextAssessment")
    hypothesis_id = assessment.get("hypothesis_id")
    if not hypothesis_id:
        raise ResearcherError("context assessment has no hypothesis_id")
    hypothesis = _required(ledger, hypothesis_id, "Hypothesis")

    critic = _required(ledger, critic_id, "CriticRecord")
    if critic.get("subject_id") != hypothesis_id:
        raise ResearcherError("critic subject does not match assessment hypothesis")
    if critic.get("assessment_id") != assessment_id:
        raise ResearcherError("critic did not review the supplied assessment")

    observation_ids = hypothesis.get("observation_ids") or []
    if not observation_ids:
        raise ResearcherError("hypothesis has no source observation")
    observation = _required(ledger, observation_ids[0], "Observation")

    artifact = observation.get("artifact")
    location = observation.get("location") or ""
    if not artifact:
        raise ResearcherError("source observation has no artifact")
    try:
        line = int(str(location).rsplit(":", 1)[1])
    except (IndexError, ValueError) as exc:
        raise ResearcherError(f"cannot derive source line from observation location: {location}") from exc

    source_id = observation.get("source_id")
    source = _required(ledger, source_id, "Source") if source_id else None
    if source is None:
        raise ResearcherError("source observation has no recorded Source")

    path = resolve_repo_artifact(root, artifact)
    current_hash = sha256_file(path)
    recorded_hash = source.get("content_hash")
    if recorded_hash and current_hash != recorded_hash:
        raise ResearcherError(
            f"source snapshot changed since signal ingestion: {artifact}"
        )

    context = collect_source_context(path, line, radius=context_radius)
    repository_data = (
        "BEGIN_UNTRUSTED_REPOSITORY_DATA\n"
        f"artifact={artifact}\n"
        f"focus_line={line}\n"
        f"content_hash={current_hash}\n"
        f"{context['text']}\n"
        "END_UNTRUSTED_REPOSITORY_DATA"
    )

    return ResearchPacket(
        hypothesis_id=hypothesis_id,
        hypothesis_statement=hypothesis.get("statement", ""),
        hypothesis_falsifier=hypothesis.get("falsifier", ""),
        hypothesis_prediction=hypothesis.get("prediction", ""),
        assessment_id=assessment_id,
        assessment_status=assessment.get("status", ""),
        assessment_rationale=assessment.get("rationale", ""),
        critic_id=critic_id,
        critic_verdict=critic.get("verdict", ""),
        critic_objections=list(critic.get("objections") or []),
        critic_missing_evidence=list(critic.get("missing_evidence") or []),
        evidence_summaries=_evidence_summaries(ledger, assessment),
        untrusted_repository_data=repository_data,
    )


def run_model_researcher(
    ledger: Ledger,
    assessment_id: str,
    critic_id: str,
    repo_root: str | Path,
    *,
    policy: ScopePolicy,
    model: ResearchModel,
    repo_commit: str | None = None,
    context_radius: int = 4,
) -> dict[str, Any]:
    """Ask a model for a schema-constrained research proposal.

    V1.6 never converts model output into Evidence, Validation, Claim, Finding, or
    a new Hypothesis. The only durable model-authored research object is a
    ResearchProposal.
    """
    ledger.init()
    packet = build_research_packet(
        ledger,
        assessment_id,
        critic_id,
        repo_root,
        policy=policy,
        context_radius=context_radius,
    )

    packet_json = json.dumps(packet.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    packet_hash = sha256_text(packet_json)

    try:
        raw_output = model.propose(packet)
        parsed = ModelProposalOutput.model_validate(raw_output)
    except (ValidationError, TypeError, ValueError) as exc:
        raise ResearcherError(f"model output failed proposal schema validation: {exc}") from exc

    output_json = json.dumps(parsed.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    output_hash = sha256_text(output_json)

    try:
        proposal_kind = ProposalKind(parsed.proposal_kind)
        disposition = ProposalDisposition(parsed.disposition)
    except ValueError as exc:
        raise ResearcherError(f"model output uses unsupported proposal enum: {exc}") from exc

    method = Method(
        name="Schema-constrained research model proposal",
        kind=MethodKind.MODEL_REASONING,
        version="1.6",
        deterministic=False,
        parameters={
            "network_controlled_by_adapter": True,
            "shell_access": False,
            "can_create_finding": False,
            "can_create_validation": False,
            "can_modify_evidence": False,
            "repository_content_boundary": "untrusted_data_only",
            "output_schema": "ModelProposalOutput/v1",
        },
        provenance=Provenance(
            created_by="researcher-harness-v1.6",
            model_id=model.model_id,
            tool_name="research-model-adapter",
            tool_version="1.6",
            repo_commit=repo_commit,
            input_hash=packet_hash,
            output_hash=output_hash,
            scope_id=policy.scope_id,
            parent_ids=[packet.hypothesis_id, assessment_id, critic_id],
        ),
    )
    ledger.put(method)

    proposal = ResearchProposal(
        subject_id=packet.hypothesis_id,
        assessment_id=assessment_id,
        critic_id=critic_id,
        method_id=method.id,
        proposal_kind=proposal_kind,
        disposition=disposition,
        statement=parsed.statement,
        falsifier=parsed.falsifier,
        prediction=parsed.prediction,
        requested_evidence=parsed.requested_evidence,
        assumptions=parsed.assumptions,
        model_output_hash=output_hash,
        repository_content_treated_as_data=True,
        schema_version=parsed.schema_version,
        provenance=Provenance(
            created_by="researcher-harness-v1.6",
            model_id=model.model_id,
            tool_name="research-model-adapter",
            tool_version="1.6",
            repo_commit=repo_commit,
            input_hash=packet_hash,
            output_hash=output_hash,
            scope_id=policy.scope_id,
            parent_ids=[packet.hypothesis_id, assessment_id, critic_id, method.id],
        ),
    )
    ledger.put(proposal)
    ledger.add_edge(proposal.id, EdgeRelation.PROPOSES_FOR, packet.hypothesis_id)
    ledger.add_edge(proposal.id, EdgeRelation.DERIVED_FROM, assessment_id)
    ledger.add_edge(proposal.id, EdgeRelation.DERIVED_FROM, critic_id)
    ledger.add_edge(proposal.id, EdgeRelation.USES_METHOD, method.id)

    audit = ledger.audit()
    if not audit["ok"]:
        raise ResearcherError(f"researcher produced invalid ledger: {audit['issues']}")

    return {
        "proposal_id": proposal.id,
        "subject_id": proposal.subject_id,
        "assessment_id": assessment_id,
        "critic_id": critic_id,
        "model_id": model.model_id,
        "proposal_kind": proposal.proposal_kind.value,
        "disposition": proposal.disposition.value,
        "requested_evidence": proposal.requested_evidence,
        "repository_content_treated_as_data": proposal.repository_content_treated_as_data,
        "packet_hash": packet_hash,
        "model_output_hash": output_hash,
        "audit": audit,
    }
