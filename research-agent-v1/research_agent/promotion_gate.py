from __future__ import annotations

import re
from typing import Any

from .ledger import Ledger, sha256_text
from .models import (
    AssessmentStatus,
    CriticVerdict,
    EdgeRelation,
    Hypothesis,
    Method,
    MethodKind,
    PromotionDecision,
    ProposalDecision,
    ProposalDisposition,
    ProposalKind,
    Provenance,
)
from .policy import ScopePolicy


class PromotionGateError(RuntimeError):
    pass


_CERTAINTY_PATTERNS = (
    re.compile(r"\bconfirmed vulnerability\b", re.I),
    re.compile(r"\bdefinitely exploitable\b", re.I),
    re.compile(r"\bproven exploitable\b", re.I),
    re.compile(r"\bCVE-\d{4}-\d+\b", re.I),
    re.compile(r"\bCVSS\s*[:=]?\s*\d", re.I),
)


def _required(ledger: Ledger, object_id: str, kind: str) -> dict[str, Any]:
    obj = ledger.get(object_id)
    if obj is None:
        raise PromotionGateError(f"unknown object: {object_id}")
    if obj["kind"] != kind:
        raise PromotionGateError(f"{object_id} is {obj['kind']}, expected {kind}")
    return obj["payload"]


def _normalize_statement(text: str) -> str:
    return " ".join(text.lower().split())


def _existing_decision_id(ledger: Ledger, proposal_id: str) -> str | None:
    with ledger.connect() as conn:
        rows = conn.execute(
            "SELECT id, payload_json FROM objects WHERE kind='ProposalDecision'"
        ).fetchall()
    import json
    for row in rows:
        payload = json.loads(row["payload_json"])
        if payload.get("proposal_id") == proposal_id:
            return row["id"]
    return None


def _duplicate_hypothesis_id(
    ledger: Ledger,
    statement: str,
    *,
    exclude_id: str | None = None,
) -> str | None:
    wanted = _normalize_statement(statement)
    with ledger.connect() as conn:
        rows = conn.execute(
            "SELECT id, payload_json FROM objects WHERE kind='Hypothesis'"
        ).fetchall()
    import json
    for row in rows:
        if row["id"] == exclude_id:
            continue
        payload = json.loads(row["payload_json"])
        if _normalize_statement(payload.get("statement", "")) == wanted:
            return row["id"]
    return None


def _has_unsupported_certainty(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in _CERTAINTY_PATTERNS)


def _lineage_check(
    proposal: dict[str, Any],
    assessment: dict[str, Any],
    critic: dict[str, Any],
    method: dict[str, Any],
) -> None:
    subject_id = proposal.get("subject_id")
    if assessment.get("hypothesis_id") != subject_id:
        raise PromotionGateError("proposal assessment targets a different hypothesis")
    if critic.get("subject_id") != subject_id:
        raise PromotionGateError("proposal critic targets a different hypothesis")
    if critic.get("assessment_id") != proposal.get("assessment_id"):
        raise PromotionGateError("proposal critic did not review the referenced assessment")
    if method.get("kind") != MethodKind.MODEL_REASONING.value:
        raise PromotionGateError("proposal method is not MODEL_REASONING")


def _decide(
    ledger: Ledger,
    proposal: dict[str, Any],
    assessment: dict[str, Any],
    critic: dict[str, Any],
    *,
    policy: ScopePolicy,
    repo_commit: str | None,
) -> tuple[PromotionDecision, list[str], str]:
    reasons: list[str] = []
    provenance = proposal.get("provenance") or {}

    if provenance.get("scope_id") != policy.scope_id:
        reasons.append("SCOPE_MISMATCH")
    if not provenance.get("model_id"):
        reasons.append("MISSING_MODEL_ID")
    if not provenance.get("input_hash") or not provenance.get("output_hash"):
        reasons.append("INCOMPLETE_MODEL_PROVENANCE")
    if proposal.get("model_output_hash") != provenance.get("output_hash"):
        reasons.append("MODEL_OUTPUT_HASH_MISMATCH")
    if proposal.get("repository_content_treated_as_data") is not True:
        reasons.append("REPOSITORY_BOUNDARY_VIOLATION")

    expected_parents = {
        proposal.get("subject_id"),
        proposal.get("assessment_id"),
        proposal.get("critic_id"),
        proposal.get("method_id"),
    }
    actual_parents = set(provenance.get("parent_ids") or [])
    if not expected_parents.issubset(actual_parents):
        reasons.append("INCOMPLETE_PARENT_LINEAGE")

    if repo_commit and provenance.get("repo_commit") and provenance.get("repo_commit") != repo_commit:
        reasons.append("STALE_REPOSITORY_COMMIT")
        return (
            PromotionDecision.DEFER,
            reasons,
            "Proposal was produced from a different repository commit and must be regenerated before promotion.",
        )

    if reasons:
        return (
            PromotionDecision.REJECT,
            reasons,
            "Proposal failed deterministic provenance or trust-boundary checks.",
        )

    assessment_status = AssessmentStatus(assessment.get("status"))
    critic_verdict = CriticVerdict(critic.get("verdict"))
    kind = ProposalKind(proposal.get("proposal_kind"))
    disposition = ProposalDisposition(proposal.get("disposition"))

    if critic_verdict == CriticVerdict.REJECTS:
        return (
            PromotionDecision.REJECT,
            ["CRITIC_REJECTS"],
            "Independent critic rejected the underlying hypothesis on current evidence.",
        )
    if assessment_status == AssessmentStatus.NO_MATCH:
        return (
            PromotionDecision.REJECT,
            ["ASSESSMENT_NO_MATCH"],
            "Deterministic contextual validation did not reproduce the scanner-reported condition.",
        )
    if disposition == ProposalDisposition.DEPRIORITIZE:
        return (
            PromotionDecision.REJECT,
            ["MODEL_DEPRIORITIZED"],
            "The proposal itself requests deprioritization rather than promotion.",
        )

    if kind == ProposalKind.EVIDENCE_REQUEST:
        if not proposal.get("requested_evidence"):
            return (
                PromotionDecision.REJECT,
                ["EMPTY_EVIDENCE_REQUEST"],
                "Evidence-request proposal contains no requested evidence.",
            )
        codes = ["EVIDENCE_REQUEST_REQUIRES_EXECUTOR"]
        if critic_verdict == CriticVerdict.CHALLENGES:
            codes.append("CRITIC_CHALLENGES")
        return (
            PromotionDecision.DEFER,
            codes,
            "Evidence requests require a separate scoped executor; the proposal gate cannot execute tools.",
        )

    if kind != ProposalKind.HYPOTHESIS_REFINEMENT:
        return (
            PromotionDecision.REJECT,
            ["UNSUPPORTED_PROPOSAL_KIND"],
            "Proposal kind is not promotable by V1.7.",
        )

    combined = " ".join(
        [proposal.get("statement", ""), proposal.get("prediction", "")]
    )
    if _has_unsupported_certainty(combined):
        return (
            PromotionDecision.REJECT,
            ["UNSUPPORTED_CERTAINTY_LANGUAGE"],
            "Proposal introduces certainty or vulnerability identifiers not established by the ledger.",
        )

    duplicate = _duplicate_hypothesis_id(
        ledger,
        proposal.get("statement", ""),
        exclude_id=proposal.get("subject_id"),
    )
    if duplicate:
        return (
            PromotionDecision.REJECT,
            ["DUPLICATE_HYPOTHESIS"],
            f"An equivalent hypothesis already exists in the ledger: {duplicate}.",
        )

    if critic_verdict == CriticVerdict.CHALLENGES or assessment_status == AssessmentStatus.INCONCLUSIVE:
        return (
            PromotionDecision.DEFER,
            ["UNRESOLVED_CRITIC_CHALLENGE"],
            "The refinement cannot be promoted until the critic's unresolved challenge is addressed.",
        )
    if assessment_status == AssessmentStatus.WEAKENED:
        return (
            PromotionDecision.DEFER,
            ["WEAKENED_ASSESSMENT"],
            "The deterministic assessment weakens the current branch; materially new evidence is required.",
        )
    if critic_verdict != CriticVerdict.SUPPORTS or assessment_status != AssessmentStatus.SUSPICIOUS:
        return (
            PromotionDecision.DEFER,
            ["INSUFFICIENT_PROMOTION_BASIS"],
            "Current assessment and critic state do not meet the V1.7 promotion basis.",
        )

    return (
        PromotionDecision.ACCEPT,
        ["STRUCTURAL_GATE_PASSED"],
        "Refinement passed deterministic lineage, trust-boundary, duplicate, and critic-state gates.",
    )


def run_proposal_gate(
    ledger: Ledger,
    proposal_id: str,
    *,
    policy: ScopePolicy,
    repo_commit: str | None = None,
) -> dict[str, Any]:
    """Deterministically gate a model-authored proposal.

    V1.7 never executes evidence requests and never creates Claim, Validation, or
    Finding objects. Only an accepted HYPOTHESIS_REFINEMENT may produce a new
    gate-authored Hypothesis.
    """
    ledger.init()

    previous_id = _existing_decision_id(ledger, proposal_id)
    if previous_id:
        payload = _required(ledger, previous_id, "ProposalDecision")
        return {
            "decision_id": previous_id,
            "proposal_id": proposal_id,
            "decision": payload["decision"],
            "reason_codes": payload.get("reason_codes") or [],
            "promoted_hypothesis_id": payload.get("promoted_hypothesis_id"),
            "idempotent_reuse": True,
            "audit": ledger.audit(),
        }

    proposal = _required(ledger, proposal_id, "ResearchProposal")
    subject = _required(ledger, proposal.get("subject_id"), "Hypothesis")
    assessment = _required(ledger, proposal.get("assessment_id"), "ContextAssessment")
    critic = _required(ledger, proposal.get("critic_id"), "CriticRecord")
    proposal_method = _required(ledger, proposal.get("method_id"), "Method")
    _lineage_check(proposal, assessment, critic, proposal_method)

    decision_value, reason_codes, rationale = _decide(
        ledger,
        proposal,
        assessment,
        critic,
        policy=policy,
        repo_commit=repo_commit,
    )

    gate_input = {
        "proposal_id": proposal_id,
        "proposal_hash": ledger.get(proposal_id)["payload_hash"],
        "subject_id": proposal.get("subject_id"),
        "assessment_id": proposal.get("assessment_id"),
        "critic_id": proposal.get("critic_id"),
        "repo_commit": repo_commit,
        "scope_id": policy.scope_id,
    }
    gate_input_hash = sha256_text(__import__("json").dumps(gate_input, sort_keys=True, separators=(",", ":")))

    method = Method(
        name="Deterministic research-proposal promotion gate",
        kind=MethodKind.PROPOSAL_GATE,
        version="1.7",
        deterministic=True,
        parameters={
            "executes_tools": False,
            "reads_repository": False,
            "can_create_finding": False,
            "can_create_validation": False,
            "accepted_object_kind": "Hypothesis",
        },
        provenance=Provenance(
            created_by="proposal-gate-v1.7",
            tool_name="proposal-gate",
            tool_version="1.7",
            repo_commit=repo_commit,
            input_hash=gate_input_hash,
            scope_id=policy.scope_id,
            parent_ids=[proposal_id, proposal.get("subject_id"), proposal.get("assessment_id"), proposal.get("critic_id")],
        ),
    )
    ledger.put(method)

    decision = ProposalDecision(
        proposal_id=proposal_id,
        subject_id=proposal.get("subject_id"),
        method_id=method.id,
        decision=decision_value,
        rationale=rationale,
        reason_codes=reason_codes,
        promoted_hypothesis_id=None,
        deterministic=True,
        gate_version="1.7",
        provenance=Provenance(
            created_by="proposal-gate-v1.7",
            tool_name="proposal-gate",
            tool_version="1.7",
            repo_commit=repo_commit,
            input_hash=gate_input_hash,
            scope_id=policy.scope_id,
            parent_ids=[proposal_id, proposal.get("subject_id"), proposal.get("assessment_id"), proposal.get("critic_id"), method.id],
        ),
    )

    promoted: Hypothesis | None = None
    if decision_value == PromotionDecision.ACCEPT:
        promoted = Hypothesis(
            statement=proposal.get("statement", ""),
            falsifier=proposal.get("falsifier", ""),
            prediction=proposal.get("prediction", ""),
            observation_ids=list(subject.get("observation_ids") or []),
            model_confidence=None,
            provenance=Provenance(
                created_by="proposal-gate-v1.7",
                tool_name="proposal-gate",
                tool_version="1.7",
                repo_commit=repo_commit,
                input_hash=gate_input_hash,
                scope_id=policy.scope_id,
                parent_ids=[proposal_id, proposal.get("subject_id"), decision.id],
            ),
        )
        decision.promoted_hypothesis_id = promoted.id

    ledger.put(decision)
    ledger.add_edge(decision.id, EdgeRelation.DECIDES_ON, proposal_id)
    ledger.add_edge(decision.id, EdgeRelation.USES_METHOD, method.id)
    ledger.add_edge(decision.id, EdgeRelation.DERIVED_FROM, proposal.get("subject_id"))

    if promoted is not None:
        ledger.put(promoted)
        ledger.add_edge(decision.id, EdgeRelation.PROMOTES_TO, promoted.id)
        ledger.add_edge(promoted.id, EdgeRelation.DERIVED_FROM, proposal_id)
        ledger.add_edge(promoted.id, EdgeRelation.DERIVED_FROM, proposal.get("subject_id"))

    audit = ledger.audit()
    if not audit["ok"]:
        raise PromotionGateError(f"proposal gate produced invalid ledger: {audit['issues']}")

    return {
        "decision_id": decision.id,
        "proposal_id": proposal_id,
        "decision": decision.decision.value,
        "reason_codes": decision.reason_codes,
        "promoted_hypothesis_id": decision.promoted_hypothesis_id,
        "idempotent_reuse": False,
        "audit": audit,
    }
