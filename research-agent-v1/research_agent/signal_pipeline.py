from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .ledger import Ledger, sha256_file, sha256_text
from .models import (
    EdgeRelation,
    Evidence,
    EvidenceRelation,
    Hypothesis,
    Method,
    MethodKind,
    Observation,
    Provenance,
    Source,
    SourceType,
)
from .policy import Capability, ScopePolicy


class SignalPipelineError(RuntimeError):
    """Raised when scanner input cannot be safely converted into research objects."""


def _prov(
    actor: str,
    *,
    tool_name: str | None = None,
    tool_version: str | None = None,
    repo_commit: str | None = None,
    scope_id: str | None = None,
    parent_ids: list[str] | None = None,
) -> Provenance:
    return Provenance(
        created_by=actor,
        tool_name=tool_name,
        tool_version=tool_version,
        repo_commit=repo_commit,
        scope_id=scope_id,
        parent_ids=parent_ids or [],
    )


def resolve_repo_artifact(repo_root: str | Path, artifact: str) -> Path:
    """Resolve an artifact path while preventing traversal and symlink escape."""
    root = Path(repo_root).resolve(strict=True)
    raw = Path(artifact)
    candidate = raw.resolve(strict=True) if raw.is_absolute() else (root / raw).resolve(strict=True)

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SignalPipelineError(
            f"scanner artifact escapes authorized repository root: {artifact}"
        ) from exc

    if not candidate.is_file():
        raise SignalPipelineError(f"scanner artifact is not a regular file: {artifact}")

    return candidate


def collect_source_context(path: Path, line: int, radius: int = 4) -> dict[str, Any]:
    if radius < 0 or radius > 50:
        raise SignalPipelineError("context radius must be between 0 and 50 lines")
    if line < 1:
        raise SignalPipelineError(f"invalid source line: {line}")

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        raise SignalPipelineError(f"artifact is empty: {path}")

    start = max(1, line - radius)
    end = min(len(lines), line + radius)
    rendered = "\n".join(
        f"{number:>6}: {lines[number - 1]}" for number in range(start, end + 1)
    )
    return {
        "start_line": start,
        "end_line": end,
        "focus_line": line,
        "text": rendered,
    }


def _hypothesis_text(check_id: str, message: str, artifact: str, line: int) -> tuple[str, str, str]:
    statement = (
        f"Semgrep signal {check_id} indicates a potential security weakness at "
        f"{artifact}:{line}: {message}"
    )
    falsifier = (
        "The reported condition is unreachable, non-user-controlled, correctly sanitized, "
        "or otherwise does not satisfy the rule's security semantics when surrounding code "
        "and data flow are independently validated."
    )
    prediction = (
        "Independent source-level validation should identify the concrete security-relevant "
        "condition described by the scanner rule at or through this location."
    )
    return statement, falsifier, prediction


def run_semgrep_signal_pipeline(
    ledger: Ledger,
    semgrep_json: str | Path,
    repo_root: str | Path,
    *,
    policy: ScopePolicy,
    repo_commit: str | None = None,
    context_radius: int = 4,
) -> dict[str, Any]:
    """Convert Semgrep output into observations and falsifiable hypothesis candidates.

    This stage deliberately creates no Claim, Validation, or Finding. Scanner output is a
    signal only. Repository text is treated as untrusted evidence data, never instructions.
    """
    policy.require(Capability.REPO_READ)
    policy.require(Capability.STATIC_SCAN)

    ledger.init()
    semgrep_path = Path(semgrep_json).resolve(strict=True)
    root = policy.require_repository(repo_root)
    data = json.loads(semgrep_path.read_text(encoding="utf-8"))

    tool = data.get("tool", {}) if isinstance(data.get("tool"), dict) else {}
    semgrep_version = tool.get("version") or data.get("version")

    scan_source = Source(
        source_type=SourceType.TOOL_OUTPUT,
        reference=str(semgrep_path),
        content_hash=sha256_file(semgrep_path),
        metadata={
            "tool": "semgrep",
            "trust_zone": "untrusted_tool_output",
            "authoritative_finding": False,
        },
        provenance=_prov(
            "semgrep-signal-pipeline",
            tool_name="filesystem",
            repo_commit=repo_commit,
            scope_id=policy.scope_id,
        ),
    )
    scan_method = Method(
        name="Semgrep static-analysis signal ingestion",
        kind=MethodKind.STATIC_ANALYSIS,
        version=str(semgrep_version) if semgrep_version else None,
        deterministic=True,
        parameters={"input_format": "semgrep-json"},
        provenance=_prov(
            "semgrep-signal-pipeline",
            tool_name="semgrep",
            tool_version=str(semgrep_version) if semgrep_version else None,
            repo_commit=repo_commit,
            scope_id=policy.scope_id,
            parent_ids=[scan_source.id],
        ),
    )
    context_method = Method(
        name="bounded source context collection",
        kind=MethodKind.PARSER,
        version="1",
        deterministic=True,
        parameters={"radius": context_radius, "network": False},
        provenance=_prov(
            "semgrep-signal-pipeline",
            tool_name="filesystem",
            repo_commit=repo_commit,
            scope_id=policy.scope_id,
        ),
    )

    for obj in (scan_source, scan_method, context_method):
        ledger.put(obj)

    candidates: list[dict[str, Any]] = []
    file_sources: dict[Path, Source] = {}

    for result in data.get("results", []):
        if not isinstance(result, dict):
            continue
        start = result.get("start", {}) or {}
        line = int(start.get("line") or 0)
        artifact = str(result.get("path") or "")
        if not artifact:
            raise SignalPipelineError("Semgrep result is missing path")
        if line < 1:
            raise SignalPipelineError(f"Semgrep result has invalid line for {artifact}: {line}")

        resolved = resolve_repo_artifact(root, artifact)
        relative = resolved.relative_to(root).as_posix()

        file_source = file_sources.get(resolved)
        if file_source is None:
            file_source = Source(
                source_type=SourceType.FILE,
                reference=relative,
                content_hash=sha256_file(resolved),
                metadata={
                    "repository_root": str(root),
                    "trust_zone": "untrusted_repository_content",
                    "authorized": True,
                },
                provenance=_prov(
                    "semgrep-signal-pipeline",
                    tool_name="filesystem",
                    repo_commit=repo_commit,
                    scope_id=policy.scope_id,
                ),
            )
            ledger.put(file_source)
            file_sources[resolved] = file_source

        extra = result.get("extra", {}) or {}
        check_id = str(result.get("check_id") or "unknown-rule")
        message = str(extra.get("message") or "Semgrep signal")
        metadata = extra.get("metadata", {}) if isinstance(extra.get("metadata"), dict) else {}

        observation = Observation(
            summary=f"{check_id}: {message}",
            artifact=relative,
            location=f"{relative}:{line}",
            source_id=file_source.id,
            method_id=scan_method.id,
            raw={
                "scanner": "semgrep",
                "check_id": check_id,
                "message": message,
                "severity": extra.get("severity"),
                "metadata": metadata,
                "raw_result": result,
                "scanner_output_source_id": scan_source.id,
            },
            provenance=_prov(
                "semgrep-signal-pipeline",
                tool_name="semgrep",
                tool_version=str(semgrep_version) if semgrep_version else None,
                repo_commit=repo_commit,
                scope_id=policy.scope_id,
                parent_ids=[scan_source.id, file_source.id, scan_method.id],
            ),
        )

        statement, falsifier, prediction = _hypothesis_text(
            check_id, message, relative, line
        )
        hypothesis = Hypothesis(
            statement=statement,
            falsifier=falsifier,
            prediction=prediction,
            observation_ids=[observation.id],
            model_confidence=None,
            provenance=_prov(
                "deterministic-hypothesis-template",
                tool_name="template",
                repo_commit=repo_commit,
                scope_id=policy.scope_id,
                parent_ids=[observation.id],
            ),
        )

        context = collect_source_context(resolved, line, radius=context_radius)
        context_payload = json.dumps(
            {"artifact": relative, **context}, sort_keys=True, separators=(",", ":")
        )
        evidence = Evidence(
            description=(
                f"Bounded source context for Semgrep signal {check_id}; this evidence is "
                "neutral until an independent validator interprets the relevant data flow."
            ),
            source_type=SourceType.FILE.value,
            source_ref=f"{relative}:{context['start_line']}-{context['end_line']}",
            relation=EvidenceRelation.NEUTRAL,
            source_id=file_source.id,
            method_id=context_method.id,
            immutable_hash=sha256_text(context_payload),
            provenance=_prov(
                "semgrep-signal-pipeline",
                tool_name="filesystem",
                repo_commit=repo_commit,
                scope_id=policy.scope_id,
                parent_ids=[observation.id, hypothesis.id, file_source.id],
            ),
        )

        for obj in (observation, hypothesis, evidence):
            ledger.put(obj)

        edges = (
            (observation.id, EdgeRelation.OBSERVED_FROM, file_source.id),
            (observation.id, EdgeRelation.REFERENCES, scan_source.id),
            (observation.id, EdgeRelation.USES_METHOD, scan_method.id),
            (hypothesis.id, EdgeRelation.MOTIVATED_BY, observation.id),
            (evidence.id, EdgeRelation.OBSERVED_FROM, file_source.id),
            (evidence.id, EdgeRelation.USES_METHOD, context_method.id),
            (evidence.id, EdgeRelation.DERIVED_FROM, observation.id),
        )
        for source_id, relation, target_id in edges:
            ledger.add_edge(source_id, relation, target_id)

        candidates.append(
            {
                "check_id": check_id,
                "artifact": relative,
                "line": line,
                "observation_id": observation.id,
                "hypothesis_id": hypothesis.id,
                "context_evidence_id": evidence.id,
                "context": context,
            }
        )

    audit = ledger.audit()
    if not audit["ok"]:
        raise SignalPipelineError(f"signal pipeline produced invalid ledger: {audit['issues']}")

    return {
        "scanner": "semgrep",
        "scanner_source_id": scan_source.id,
        "scanner_method_id": scan_method.id,
        "context_method_id": context_method.id,
        "repo_root": str(root),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "audit": audit,
    }
