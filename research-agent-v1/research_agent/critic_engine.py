from __future__ import annotations

from typing import Any

from .ledger import Ledger
from .models import (
    AssessmentStatus,
    CriticRecord,
    CriticVerdict,
    EdgeRelation,
    Method,
    MethodKind,
    Provenance,
)


class CriticError(RuntimeError):
    pass


def _get_required(ledger: Ledger, object_id: str, kind: str) -> dict[str, Any]:
    obj = ledger.get(object_id)
    if obj is None:
        raise CriticError(f"unknown object: {object_id}")
    if obj["kind"] != kind:
        raise CriticError(f"{object_id} is {obj['kind']}, expected {kind}")
    return obj["payload"]


def _evidence_payloads(ledger: Ledger, ids: list[str]) -> list[dict[str, Any]]:
    payloads = []
    for evidence_id in ids:
        payloads.append(_get_required(ledger, evidence_id, "Evidence"))
    return payloads


def _fact_types(evidence: list[dict[str, Any]]) -> set[str]:
    return {
        str((item.get("metadata") or {}).get("fact_type"))
        for item in evidence
        if (item.get("metadata") or {}).get("fact_type")
    }


def run_independent_critic(
    ledger: Ledger,
    assessment_id: str,
    *,
    repo_commit: str | None = None,
) -> dict[str, Any]:
    """Review one ContextAssessment using ledger evidence only.

    V1.5 intentionally does not read repository files, execute tools, create a
    Validation, or create/promote a Finding. Its job is to attack the hypothesis
    using the validator's recorded evidence and to state what is still missing.
    """
    ledger.init()
    assessment = _get_required(ledger, assessment_id, "ContextAssessment")
    hypothesis_id = assessment.get("hypothesis_id")
    if not hypothesis_id:
        raise CriticError("context assessment has no hypothesis_id")
    hypothesis = _get_required(ledger, hypothesis_id, "Hypothesis")

    assessment_actor = (assessment.get("provenance") or {}).get("created_by")
    if assessment_actor == "independent-critic-v1.5":
        raise CriticError("critic cannot independently review its own assessment")

    evidence_ids = list(dict.fromkeys(
        (assessment.get("supporting_evidence_ids") or [])
        + (assessment.get("contradictory_evidence_ids") or [])
        + (assessment.get("neutral_evidence_ids") or [])
    ))
    evidence = _evidence_payloads(ledger, evidence_ids)
    facts = _fact_types(evidence)
    status = AssessmentStatus(assessment["status"])

    objections: list[str] = []
    missing: list[str] = []
    alternatives: list[str] = []
    limitations = [
        "Critic reads ledger evidence only and does not inspect repository content directly.",
        "Verdict is epistemic triage, not vulnerability confirmation.",
    ]

    if status == AssessmentStatus.SUSPICIOUS:
        source_fact = bool({"SOURCE_CANDIDATE", "INDIRECT_SOURCE_CANDIDATE"} & facts)
        sink_fact = "SINK" in facts
        if source_fact and sink_fact:
            verdict = CriticVerdict.SUPPORTS
            objections.append(
                "Function-parameter origin is not equivalent to attacker-controlled reachability."
            )
            missing.extend(
                [
                    "Call-site or trust-boundary evidence showing external influence over the candidate parameter.",
                    "Interprocedural evidence that no effective validation constrains the value before this function.",
                ]
            )
            alternatives.append(
                "All reachable callers may supply only trusted or prevalidated values."
            )
        else:
            verdict = CriticVerdict.INCONCLUSIVE
            objections.append(
                "Assessment is SUSPICIOUS but lacks the expected deterministic source/sink fact pair."
            )
            missing.append("Consistent source and sink evidence for the assessed signal.")

    elif status == AssessmentStatus.WEAKENED:
        if "CONSTANT_INPUT" in facts:
            verdict = CriticVerdict.REJECTS
            objections.append(
                "The current source snapshot resolves the eval input to a literal constant."
            )
            alternatives.append(
                "The scanner correctly identified eval usage, but this occurrence does not support the user-controlled-input hypothesis."
            )
        elif "UNREACHABLE_LITERAL_BRANCH" in facts:
            verdict = CriticVerdict.REJECTS
            objections.append(
                "The current sink is inside a deterministically unreachable literal branch."
            )
            alternatives.append(
                "The scanner signal can be syntactically true while the reported path is unreachable in this snapshot."
            )
        else:
            verdict = CriticVerdict.CHALLENGES
            objections.append("Contradictory evidence materially weakens the hypothesis.")
            missing.append("Additional evidence resolving the contradiction.")

    elif status == AssessmentStatus.NO_MATCH:
        verdict = CriticVerdict.REJECTS
        objections.append(
            "The current source snapshot does not contain the scanner-reported sink at the recorded location."
        )
        alternatives.append(
            "Scanner output may be stale, mismatched to the source snapshot, or generated from different code."
        )

    else:  # INCONCLUSIVE
        if "GUARD_CANDIDATE" in facts:
            verdict = CriticVerdict.CHALLENGES
            objections.append(
                "A guard references the candidate input, and its security semantics have not been resolved."
            )
            missing.extend(
                [
                    "Semantic proof of what values the guard permits.",
                    "Evidence that the guard dominates the sink on the relevant execution path.",
                ]
            )
            alternatives.extend(
                [
                    "The guard may effectively constrain the input.",
                    "The guard may be incomplete or bypassable; V1.5 does not infer either outcome."
                ]
            )
        else:
            verdict = CriticVerdict.INCONCLUSIVE
            objections.append("The deterministic context assessment did not resolve the hypothesis.")
            if "UNKNOWN_INPUT_ORIGIN" in facts:
                missing.append("Interprocedural or broader data-flow evidence for input origin.")
            elif "UNSUPPORTED_RULE" in facts:
                missing.append("A deterministic validator for this scanner rule family.")
            else:
                missing.append("Additional evidence sufficient to test the hypothesis falsifier.")

    method = Method(
        name="Independent ledger-only critic",
        kind=MethodKind.CRITIC_REVIEW,
        version="1.5",
        deterministic=True,
        parameters={
            "reads_repository": False,
            "network": False,
            "input_boundary": "ledger_context_assessment_only",
            "can_create_validation": False,
            "can_create_finding": False,
        },
        provenance=Provenance(
            created_by="independent-critic-v1.5",
            tool_name="critic-rule-engine",
            tool_version="1.5",
            repo_commit=repo_commit,
            scope_id=(assessment.get("provenance") or {}).get("scope_id"),
            parent_ids=[assessment_id, hypothesis_id, *evidence_ids],
        ),
    )
    ledger.put(method)

    critic = CriticRecord(
        subject_id=hypothesis_id,
        assessment_id=assessment_id,
        method_id=method.id,
        evidence_ids=evidence_ids,
        verdict=verdict,
        objections=objections,
        missing_evidence=missing,
        alternative_explanations=alternatives,
        limitations=limitations,
        provenance=Provenance(
            created_by="independent-critic-v1.5",
            tool_name="critic-rule-engine",
            tool_version="1.5",
            repo_commit=repo_commit,
            scope_id=(assessment.get("provenance") or {}).get("scope_id"),
            parent_ids=[assessment_id, hypothesis_id, method.id, *evidence_ids],
        ),
    )
    ledger.put(critic)
    ledger.add_edge(critic.id, EdgeRelation.CRITICIZES, hypothesis_id)
    ledger.add_edge(critic.id, EdgeRelation.DERIVED_FROM, assessment_id)
    ledger.add_edge(critic.id, EdgeRelation.USES_METHOD, method.id)
    for evidence_id in evidence_ids:
        ledger.add_edge(critic.id, EdgeRelation.REFERENCES, evidence_id)

    audit = ledger.audit()
    if not audit["ok"]:
        raise CriticError(f"critic produced invalid ledger: {audit['issues']}")

    return {
        "critic_id": critic.id,
        "hypothesis_id": hypothesis_id,
        "assessment_id": assessment_id,
        "verdict": verdict.value,
        "objections": objections,
        "missing_evidence": missing,
        "alternative_explanations": alternatives,
        "limitations": limitations,
        "evidence_ids": evidence_ids,
        "audit": audit,
    }
