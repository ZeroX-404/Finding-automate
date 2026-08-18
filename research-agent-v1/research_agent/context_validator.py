from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from .ledger import Ledger, sha256_file, sha256_text
from .models import (
    AssessmentStatus,
    ContextAssessment,
    EdgeRelation,
    Evidence,
    EvidenceRelation,
    Method,
    MethodKind,
    Provenance,
    SourceType,
)
from .policy import Capability, ScopePolicy
from .signal_pipeline import resolve_repo_artifact


class ContextValidationError(RuntimeError):
    """Raised when deterministic contextual validation cannot be performed safely."""


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


def _node_contains(container: ast.AST, target: ast.AST) -> bool:
    return any(node is target for node in ast.walk(container))


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _enclosing_function(
    node: ast.AST, parents: dict[ast.AST, ast.AST]
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current
    return None


def _is_eval_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "eval"
    )


def _find_eval_call(tree: ast.AST, signal_line: int) -> ast.Call | None:
    matches: list[ast.Call] = []
    for node in ast.walk(tree):
        if not _is_eval_call(node):
            continue
        start = getattr(node, "lineno", -1)
        end = getattr(node, "end_lineno", start)
        if start <= signal_line <= end:
            matches.append(node)
    if not matches:
        return None
    return min(matches, key=lambda node: (abs(node.lineno - signal_line), node.col_offset))


def _function_parameters(
    function: ast.FunctionDef | ast.AsyncFunctionDef | None,
) -> set[str]:
    if function is None:
        return set()
    args = function.args
    names = {arg.arg for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs)}
    if args.vararg:
        names.add(args.vararg.arg)
    if args.kwarg:
        names.add(args.kwarg.arg)
    return names


def _assignment_for_name(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    name: str,
    before_line: int,
) -> tuple[ast.AST, int] | None:
    candidates: list[tuple[int, ast.AST]] = []
    for node in ast.walk(function):
        line = getattr(node, "lineno", 0)
        if not line or line >= before_line:
            continue
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    candidates.append((line, node.value))
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == name and node.value:
                candidates.append((line, node.value))
    if not candidates:
        return None
    line, value = max(candidates, key=lambda item: item[0])
    return value, line


def _names_in(node: ast.AST) -> set[str]:
    return {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}


def _resolve_origin(
    expression: ast.AST,
    function: ast.FunctionDef | ast.AsyncFunctionDef | None,
    before_line: int,
    *,
    seen: set[str] | None = None,
    depth: int = 0,
) -> dict[str, Any]:
    if depth > 8:
        return {"kind": "UNKNOWN", "symbols": [], "path": []}

    if isinstance(expression, ast.Constant):
        return {
            "kind": "CONSTANT",
            "symbols": [],
            "path": [],
            "value_repr": repr(expression.value)[:200],
        }

    parameters = _function_parameters(function)

    if isinstance(expression, ast.Name):
        name = expression.id
        if name in parameters:
            return {"kind": "PARAMETER", "symbols": [name], "path": [name]}
        if function is None:
            return {"kind": "UNKNOWN", "symbols": [name], "path": [name]}

        seen = set(seen or set())
        if name in seen:
            return {"kind": "UNKNOWN", "symbols": [name], "path": [name]}
        seen.add(name)

        assignment = _assignment_for_name(function, name, before_line)
        if assignment is None:
            return {"kind": "UNKNOWN", "symbols": [name], "path": [name]}

        value, assignment_line = assignment
        origin = _resolve_origin(
            value,
            function,
            assignment_line,
            seen=seen,
            depth=depth + 1,
        )
        origin["path"] = [name, *origin.get("path", [])]
        origin["assignment_line"] = assignment_line
        if origin.get("kind") == "PARAMETER":
            origin["kind"] = "INDIRECT_PARAMETER"
        return origin

    expression_names = _names_in(expression)
    parameter_names = sorted(expression_names & parameters)
    if parameter_names:
        return {
            "kind": "PARAMETER_EXPRESSION",
            "symbols": parameter_names,
            "path": parameter_names,
        }

    return {
        "kind": "UNKNOWN_EXPRESSION",
        "symbols": sorted(expression_names),
        "path": sorted(expression_names),
    }


def _literal_unreachable(
    sink: ast.Call, parents: dict[ast.AST, ast.AST]
) -> tuple[bool, int | None]:
    current: ast.AST = sink
    while current in parents:
        parent = parents[current]
        if isinstance(parent, ast.If) and isinstance(parent.test, ast.Constant):
            value = parent.test.value
            if value is False and any(_node_contains(item, sink) for item in parent.body):
                return True, parent.lineno
            if value is True and any(_node_contains(item, sink) for item in parent.orelse):
                return True, parent.lineno
        current = parent
    return False, None


def _guard_candidates(
    function: ast.FunctionDef | ast.AsyncFunctionDef | None,
    sink_line: int,
    symbols: set[str],
) -> list[dict[str, Any]]:
    if function is None or not symbols:
        return []

    guards: list[dict[str, Any]] = []
    for node in ast.walk(function):
        if getattr(node, "lineno", sink_line) >= sink_line:
            continue
        test: ast.AST | None = None
        kind: str | None = None
        if isinstance(node, ast.If):
            test = node.test
            kind = "IF_GUARD"
        elif isinstance(node, ast.Assert):
            test = node.test
            kind = "ASSERT_GUARD"
        if test is None:
            continue
        referenced = _names_in(test) & symbols
        if referenced:
            guards.append(
                {
                    "kind": kind,
                    "line": node.lineno,
                    "symbols": sorted(referenced),
                    "test": ast.unparse(test)[:500],
                }
            )
    return sorted(guards, key=lambda guard: guard["line"])


def _get_required_object(ledger: Ledger, object_id: str, expected_kind: str) -> dict[str, Any]:
    obj = ledger.get(object_id)
    if obj is None:
        raise ContextValidationError(f"unknown object: {object_id}")
    if obj["kind"] != expected_kind:
        raise ContextValidationError(
            f"{object_id} is {obj['kind']}, expected {expected_kind}"
        )
    return obj["payload"]


def run_python_contextual_validator(
    ledger: Ledger,
    hypothesis_id: str,
    repo_root: str | Path,
    *,
    policy: ScopePolicy,
    repo_commit: str | None = None,
) -> dict[str, Any]:
    """Deterministically assess a Python Semgrep hypothesis using AST evidence.

    Repository content is parsed as hostile data. This stage never creates a Claim,
    Validation, or Finding and never treats a detected guard as proof of safety.
    """
    policy.require(Capability.REPO_READ)
    policy.require(Capability.STATIC_SCAN)
    ledger.init()
    root = policy.require_repository(repo_root)

    hypothesis = _get_required_object(ledger, hypothesis_id, "Hypothesis")
    observation_ids = hypothesis.get("observation_ids") or []
    if len(observation_ids) != 1:
        raise ContextValidationError(
            "contextual validator currently requires exactly one originating observation"
        )

    observation_id = observation_ids[0]
    observation = _get_required_object(ledger, observation_id, "Observation")
    source_id = observation.get("source_id")
    if not source_id:
        raise ContextValidationError("observation does not reference a source")
    source = _get_required_object(ledger, source_id, "Source")

    artifact = observation.get("artifact") or source.get("reference")
    if not artifact:
        raise ContextValidationError("observation does not identify a repository artifact")
    path = resolve_repo_artifact(root, artifact)

    expected_hash = source.get("content_hash")
    current_hash = sha256_file(path)
    if expected_hash and current_hash != expected_hash:
        raise ContextValidationError(
            f"source changed since signal ingestion: {artifact}; re-run scanner ingestion"
        )

    raw = observation.get("raw") or {}
    check_id = str(raw.get("check_id") or "")
    location = observation.get("location") or ""
    try:
        signal_line = int(str(location).rsplit(":", 1)[1])
    except (IndexError, ValueError) as exc:
        raise ContextValidationError(f"cannot parse observation location: {location}") from exc

    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text, filename=artifact)
    except SyntaxError as exc:
        raise ContextValidationError(f"cannot parse Python AST for {artifact}: {exc}") from exc

    method = Method(
        name="Python AST contextual validator",
        kind=MethodKind.PARSER,
        version="1",
        deterministic=True,
        parameters={
            "language": "python",
            "network": False,
            "rule_family": "eval",
            "repository_content_trust": "untrusted_data",
        },
        provenance=_prov(
            "contextual-validator",
            tool_name="python-ast",
            tool_version="stdlib",
            repo_commit=repo_commit,
            scope_id=policy.scope_id,
            parent_ids=[hypothesis_id, observation_id, source_id],
        ),
    )
    ledger.put(method)

    evidence: list[Evidence] = []

    def add_fact(
        *,
        fact_type: str,
        description: str,
        relation: EvidenceRelation,
        line: int,
        metadata: dict[str, Any] | None = None,
    ) -> Evidence:
        fact_metadata = {
            "fact_type": fact_type,
            "basis": "PYTHON_AST",
            "deterministic": True,
            **(metadata or {}),
        }
        canonical = json.dumps(
            {
                "artifact": artifact,
                "line": line,
                "relation": relation.value,
                "metadata": fact_metadata,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        item = Evidence(
            description=description,
            source_type=SourceType.FILE.value,
            source_ref=f"{artifact}:{line}",
            relation=relation,
            source_id=source_id,
            method_id=method.id,
            immutable_hash=sha256_text(canonical),
            metadata=fact_metadata,
            provenance=_prov(
                "contextual-validator",
                tool_name="python-ast",
                tool_version="stdlib",
                repo_commit=repo_commit,
                scope_id=policy.scope_id,
                parent_ids=[hypothesis_id, observation_id, source_id, method.id],
            ),
        )
        ledger.put(item)
        ledger.add_edge(item.id, EdgeRelation.BEARS_ON, hypothesis_id)
        ledger.add_edge(item.id, EdgeRelation.OBSERVED_FROM, source_id)
        ledger.add_edge(item.id, EdgeRelation.USES_METHOD, method.id)
        if relation == EvidenceRelation.SUPPORTS:
            ledger.add_edge(item.id, EdgeRelation.SUPPORTS, hypothesis_id)
        elif relation == EvidenceRelation.CONTRADICTS:
            ledger.add_edge(item.id, EdgeRelation.CONTRADICTS, hypothesis_id)
        evidence.append(item)
        return item

    # V1.4 intentionally only gives semantic interpretation to eval-family signals.
    if "eval" not in check_id.lower():
        add_fact(
            fact_type="UNSUPPORTED_RULE",
            description=f"V1.4 has no deterministic contextual rule for {check_id}.",
            relation=EvidenceRelation.NEUTRAL,
            line=signal_line,
            metadata={"check_id": check_id},
        )
        status = AssessmentStatus.INCONCLUSIVE
        rationale = "No deterministic contextual validator is implemented for this rule family."
    else:
        sink = _find_eval_call(tree, signal_line)
        if sink is None:
            add_fact(
                fact_type="SIGNAL_MISMATCH",
                description="No eval() AST call exists at the scanner-reported source location.",
                relation=EvidenceRelation.CONTRADICTS,
                line=signal_line,
                metadata={"check_id": check_id},
            )
            status = AssessmentStatus.NO_MATCH
            rationale = "Scanner signal does not match an eval() call in the current source snapshot."
        else:
            sink_line = sink.lineno
            add_fact(
                fact_type="SINK",
                description="AST confirms an eval() call at the reported location.",
                relation=EvidenceRelation.NEUTRAL,
                line=sink_line,
                metadata={"symbol": "eval"},
            )

            parents = _parent_map(tree)
            function = _enclosing_function(sink, parents)
            unreachable, unreachable_line = _literal_unreachable(sink, parents)

            if unreachable:
                add_fact(
                    fact_type="UNREACHABLE_LITERAL_BRANCH",
                    description="eval() is inside a branch that is syntactically unreachable because its condition is a literal constant.",
                    relation=EvidenceRelation.CONTRADICTS,
                    line=unreachable_line or sink_line,
                    metadata={"sink_line": sink_line},
                )
                status = AssessmentStatus.WEAKENED
                rationale = "The reported sink is in a deterministically unreachable literal branch."
            elif not sink.args:
                add_fact(
                    fact_type="MISSING_ARGUMENT",
                    description="eval() call has no positional argument available for origin analysis.",
                    relation=EvidenceRelation.NEUTRAL,
                    line=sink_line,
                )
                status = AssessmentStatus.INCONCLUSIVE
                rationale = "Input origin cannot be determined from this call shape."
            else:
                origin = _resolve_origin(sink.args[0], function, sink_line)
                kind = origin["kind"]
                symbols = set(origin.get("symbols") or [])

                if kind == "CONSTANT":
                    add_fact(
                        fact_type="CONSTANT_INPUT",
                        description="eval() input resolves to a literal constant in the local AST slice.",
                        relation=EvidenceRelation.CONTRADICTS,
                        line=sink_line,
                        metadata={"value_repr": origin.get("value_repr")},
                    )
                    status = AssessmentStatus.WEAKENED
                    rationale = "The current eval() argument is deterministic constant input, weakening the user-controlled-input hypothesis."
                elif kind in {"PARAMETER", "INDIRECT_PARAMETER", "PARAMETER_EXPRESSION"}:
                    add_fact(
                        fact_type=(
                            "INDIRECT_SOURCE_CANDIDATE"
                            if kind == "INDIRECT_PARAMETER"
                            else "SOURCE_CANDIDATE"
                        ),
                        description="eval() input resolves to a function parameter or an expression containing a function parameter.",
                        relation=EvidenceRelation.SUPPORTS,
                        line=sink_line,
                        metadata={
                            "origin_kind": kind,
                            "symbols": sorted(symbols),
                            "resolution_path": origin.get("path", []),
                            "assignment_line": origin.get("assignment_line"),
                        },
                    )
                    guards = _guard_candidates(function, sink_line, symbols)
                    for guard in guards:
                        add_fact(
                            fact_type="GUARD_CANDIDATE",
                            description=(
                                "A preceding syntactic guard references the candidate input. "
                                "Its security semantics are not proven by V1.4."
                            ),
                            relation=EvidenceRelation.NEUTRAL,
                            line=guard["line"],
                            metadata={
                                **guard,
                                "candidate_relation": "CONTRADICTS",
                                "semantics_proven": False,
                            },
                        )
                    if guards:
                        status = AssessmentStatus.INCONCLUSIVE
                        rationale = "Parameter-derived input reaches eval(), but a preceding guard candidate requires semantic validation."
                    else:
                        status = AssessmentStatus.SUSPICIOUS
                        rationale = "Parameter-derived input reaches eval() with no syntactic guard candidate detected before the sink."
                else:
                    add_fact(
                        fact_type="UNKNOWN_INPUT_ORIGIN",
                        description="AST could not deterministically resolve eval() input to a constant or function parameter.",
                        relation=EvidenceRelation.NEUTRAL,
                        line=sink_line,
                        metadata={
                            "origin_kind": kind,
                            "symbols": sorted(symbols),
                            "resolution_path": origin.get("path", []),
                        },
                    )
                    status = AssessmentStatus.INCONCLUSIVE
                    rationale = "Input origin remains unresolved by the bounded deterministic analysis."

    supporting_ids = [item.id for item in evidence if item.relation == EvidenceRelation.SUPPORTS]
    contradictory_ids = [item.id for item in evidence if item.relation == EvidenceRelation.CONTRADICTS]
    neutral_ids = [item.id for item in evidence if item.relation == EvidenceRelation.NEUTRAL]

    assessment = ContextAssessment(
        hypothesis_id=hypothesis_id,
        status=status,
        rationale=rationale,
        supporting_evidence_ids=supporting_ids,
        contradictory_evidence_ids=contradictory_ids,
        neutral_evidence_ids=neutral_ids,
        provenance=_prov(
            "contextual-validator",
            tool_name="python-ast",
            tool_version="stdlib",
            repo_commit=repo_commit,
            scope_id=policy.scope_id,
            parent_ids=[hypothesis_id, observation_id, source_id, method.id, *[item.id for item in evidence]],
        ),
    )
    ledger.put(assessment)
    ledger.add_edge(assessment.id, EdgeRelation.ASSESSES, hypothesis_id)
    ledger.add_edge(assessment.id, EdgeRelation.USES_METHOD, method.id)
    for item in evidence:
        ledger.add_edge(assessment.id, EdgeRelation.DERIVED_FROM, item.id)

    audit = ledger.audit()
    if not audit["ok"]:
        raise ContextValidationError(
            f"contextual validator produced invalid ledger: {audit['issues']}"
        )

    return {
        "hypothesis_id": hypothesis_id,
        "observation_id": observation_id,
        "assessment_id": assessment.id,
        "status": status.value,
        "rationale": rationale,
        "supporting_evidence_ids": supporting_ids,
        "contradictory_evidence_ids": contradictory_ids,
        "neutral_evidence_ids": neutral_ids,
        "facts": [item.metadata for item in evidence],
        "audit": audit,
    }
