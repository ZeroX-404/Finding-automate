from __future__ import annotations

import ast
import json
from enum import StrEnum
from pathlib import Path
from typing import Any

from .ledger import Ledger, sha256_file, sha256_text
from .models import (
    EdgeRelation,
    Evidence,
    EvidenceRelation,
    Experiment,
    ExperimentStatus,
    Method,
    MethodKind,
    ProposalDisposition,
    ProposalKind,
    Provenance,
    SourceType,
)
from .policy import Capability, ScopePolicy
from .signal_pipeline import resolve_repo_artifact


class EvidenceExecutorError(RuntimeError):
    pass


class EvidenceOperation(StrEnum):
    SOURCE_CONTEXT = "SOURCE_CONTEXT"
    CALL_SITE_SEARCH = "CALL_SITE_SEARCH"
    SYMBOL_REFERENCE_SEARCH = "SYMBOL_REFERENCE_SEARCH"
    INTERPROCEDURAL_TRACE = "INTERPROCEDURAL_TRACE"
    GUARD_ANALYSIS = "GUARD_ANALYSIS"


MAX_PYTHON_FILES = 500
MAX_FILE_BYTES = 512 * 1024
MAX_RESULTS = 200


def classify_evidence_request(request: str) -> EvidenceOperation | None:
    """Map natural-language evidence requests to a closed operation registry.

    There is intentionally no generic command, shell, subprocess, eval, import,
    or model-selected tool fallback.
    """
    text = " ".join((request or "").lower().split())
    if not text:
        return None
    if "interprocedural" in text or "broader data-flow" in text or "data-flow" in text:
        return EvidenceOperation.INTERPROCEDURAL_TRACE
    if "call-site" in text or "call site" in text or "trust-boundary" in text or "trust boundary" in text:
        return EvidenceOperation.CALL_SITE_SEARCH
    if "guard" in text or "allowed values" in text or "permits" in text or "dominates the sink" in text:
        return EvidenceOperation.GUARD_ANALYSIS
    if "symbol reference" in text or "references to" in text:
        return EvidenceOperation.SYMBOL_REFERENCE_SEARCH
    if "source context" in text or "surrounding source" in text:
        return EvidenceOperation.SOURCE_CONTEXT
    return None


def _required(ledger: Ledger, object_id: str, kind: str) -> dict[str, Any]:
    obj = ledger.get(object_id)
    if obj is None:
        raise EvidenceExecutorError(f"unknown object: {object_id}")
    if obj["kind"] != kind:
        raise EvidenceExecutorError(f"{object_id} is {obj['kind']}, expected {kind}")
    return obj["payload"]


def _decision_for_proposal(ledger: Ledger, proposal_id: str) -> tuple[str, dict[str, Any]]:
    with ledger.connect() as conn:
        rows = conn.execute(
            "SELECT id, payload_json FROM objects WHERE kind='ProposalDecision' ORDER BY created_at"
        ).fetchall()
    matches: list[tuple[str, dict[str, Any]]] = []
    for row in rows:
        payload = json.loads(row["payload_json"])
        if payload.get("proposal_id") == proposal_id:
            matches.append((row["id"], payload))
    if not matches:
        raise EvidenceExecutorError(
            "proposal has no ProposalDecision; run the proposal gate before evidence execution"
        )
    # V1.7 gate is idempotent, so more than one durable decision is an integrity problem.
    if len(matches) != 1:
        raise EvidenceExecutorError(
            f"proposal has {len(matches)} ProposalDecision objects; expected exactly one"
        )
    return matches[0]


def _focus_context(
    ledger: Ledger,
    hypothesis_id: str,
    repo_root: Path,
) -> dict[str, Any]:
    hypothesis = _required(ledger, hypothesis_id, "Hypothesis")
    observation_ids = hypothesis.get("observation_ids") or []
    if not observation_ids:
        raise EvidenceExecutorError("hypothesis has no source observation")
    observation = _required(ledger, observation_ids[0], "Observation")
    artifact = observation.get("artifact")
    location = observation.get("location") or ""
    source_id = observation.get("source_id")
    if not artifact or not source_id:
        raise EvidenceExecutorError("source observation is missing artifact or source_id")
    try:
        focus_line = int(str(location).rsplit(":", 1)[1])
    except (IndexError, ValueError) as exc:
        raise EvidenceExecutorError(f"invalid observation location: {location}") from exc

    source = _required(ledger, source_id, "Source")
    path = resolve_repo_artifact(repo_root, artifact)
    current_hash = sha256_file(path)
    recorded_hash = source.get("content_hash")
    if recorded_hash and current_hash != recorded_hash:
        raise EvidenceExecutorError(
            f"source snapshot changed since signal ingestion: {artifact}"
        )

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        raise EvidenceExecutorError(f"cannot parse source artifact {artifact}: {exc}") from exc

    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and getattr(node, "lineno", 0) <= focus_line <= getattr(node, "end_lineno", node.lineno)
    ]
    function = min(
        functions,
        key=lambda n: getattr(n, "end_lineno", n.lineno) - n.lineno,
        default=None,
    )
    if function is None:
        raise EvidenceExecutorError(
            f"focus line {focus_line} is not inside a Python function in {artifact}"
        )

    calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and getattr(node, "lineno", 0) <= focus_line <= getattr(node, "end_lineno", node.lineno)
    ]
    sink_call = min(calls, key=lambda n: abs(getattr(n, "lineno", focus_line) - focus_line), default=None)

    parameters = [arg.arg for arg in function.args.posonlyargs + function.args.args + function.args.kwonlyargs]
    focus_symbol: str | None = None
    if sink_call and sink_call.args:
        arg = sink_call.args[0]
        if isinstance(arg, ast.Name):
            focus_symbol = arg.id

    parameter_index: int | None = None
    if focus_symbol in parameters:
        parameter_index = parameters.index(focus_symbol)
    elif focus_symbol:
        # Resolve a simple local alias, e.g. value = expression; eval(value).
        for node in ast.walk(function):
            if not isinstance(node, ast.Assign) or getattr(node, "lineno", 0) >= focus_line:
                continue
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                continue
            if node.targets[0].id == focus_symbol and isinstance(node.value, ast.Name):
                if node.value.id in parameters:
                    parameter_index = parameters.index(node.value.id)
                    break

    return {
        "hypothesis": hypothesis,
        "observation": observation,
        "artifact": artifact,
        "path": path,
        "source_id": source_id,
        "content_hash": current_hash,
        "focus_line": focus_line,
        "tree": tree,
        "function": function,
        "function_name": function.name,
        "parameters": parameters,
        "focus_symbol": focus_symbol,
        "parameter_index": parameter_index,
        "source_text": text,
    }


def _bounded_python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for candidate in sorted(root.rglob("*.py")):
        resolved = candidate.resolve(strict=True)
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise EvidenceExecutorError(f"repository Python path escapes root: {candidate}") from exc
        if not resolved.is_file() or resolved.is_symlink():
            continue
        if resolved.stat().st_size > MAX_FILE_BYTES:
            continue
        files.append(resolved)
        if len(files) > MAX_PYTHON_FILES:
            raise EvidenceExecutorError(
                f"repository exceeds bounded Python file limit ({MAX_PYTHON_FILES})"
            )
    return files


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _safe_unparse(node: ast.AST) -> str:
    try:
        value = ast.unparse(node)
    except Exception:
        value = ast.dump(node, include_attributes=False)
    return value[:240]


def _containing_function(tree: ast.AST, line: int) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    funcs = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.lineno <= line <= getattr(node, "end_lineno", node.lineno)
    ]
    return min(funcs, key=lambda n: getattr(n, "end_lineno", n.lineno) - n.lineno, default=None)


def _origin(node: ast.AST, caller: ast.FunctionDef | ast.AsyncFunctionDef | None) -> str:
    if isinstance(node, ast.Constant):
        return "LITERAL"
    if isinstance(node, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
        return "LITERAL_CONTAINER"
    if isinstance(node, ast.Call):
        return "CALL_RESULT"
    if isinstance(node, ast.Attribute):
        return "ATTRIBUTE"
    if isinstance(node, ast.Name):
        if caller is not None:
            params = {
                arg.arg
                for arg in caller.args.posonlyargs + caller.args.args + caller.args.kwonlyargs
            }
            if node.id in params:
                return "CALLER_PARAMETER"
        return "NAME"
    return type(node).__name__.upper()


def _call_sites(root: Path, function_name: str, parameter_index: int | None) -> dict[str, Any]:
    sites: list[dict[str, Any]] = []
    parse_errors: list[str] = []
    files_scanned = 0
    for path in _bounded_python_files(root):
        files_scanned += 1
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
        except SyntaxError:
            parse_errors.append(path.relative_to(root).as_posix())
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or _call_name(node.func) != function_name:
                continue
            caller = _containing_function(tree, node.lineno)
            selected = None
            if parameter_index is not None and parameter_index < len(node.args):
                selected = node.args[parameter_index]
            sites.append(
                {
                    "artifact": path.relative_to(root).as_posix(),
                    "line": node.lineno,
                    "caller": caller.name if caller else "<module>",
                    "arguments": [_safe_unparse(arg) for arg in node.args[:8]],
                    "selected_argument": _safe_unparse(selected) if selected is not None else None,
                    "selected_origin": _origin(selected, caller) if selected is not None else "MISSING_OR_UNKNOWN",
                }
            )
            if len(sites) >= MAX_RESULTS:
                break
        if len(sites) >= MAX_RESULTS:
            break
    return {
        "fact_type": "CALL_SITE_FACTS",
        "function": function_name,
        "parameter_index": parameter_index,
        "files_scanned": files_scanned,
        "parse_error_count": len(parse_errors),
        "call_site_count": len(sites),
        "truncated": len(sites) >= MAX_RESULTS,
        "call_sites": sites,
    }


def _interprocedural_trace(root: Path, focus: dict[str, Any]) -> dict[str, Any]:
    result = _call_sites(root, focus["function_name"], focus["parameter_index"])
    result["fact_type"] = "INTERPROCEDURAL_TRACE_FACTS"
    result["focus_symbol"] = focus["focus_symbol"]
    result["function_parameters"] = focus["parameters"]
    origins = sorted({site["selected_origin"] for site in result["call_sites"]})
    result["observed_argument_origins"] = origins
    result["external_control_proven"] = False
    result["note"] = (
        "Argument-origin categories are syntactic facts only; they do not establish attacker control or exploitability."
    )
    return result


def _guard_analysis(focus: dict[str, Any]) -> dict[str, Any]:
    function = focus["function"]
    symbol = focus["focus_symbol"]
    sink_line = focus["focus_line"]
    guards: list[dict[str, Any]] = []
    if symbol:
        for node in ast.walk(function):
            if not isinstance(node, ast.If) or node.lineno >= sink_line:
                continue
            names = {n.id for n in ast.walk(node.test) if isinstance(n, ast.Name)}
            if symbol not in names:
                continue
            terminates = any(isinstance(n, (ast.Raise, ast.Return)) for stmt in node.body for n in ast.walk(stmt))
            guards.append(
                {
                    "line": node.lineno,
                    "test": _safe_unparse(node.test),
                    "mentions_focus_symbol": True,
                    "reject_branch_has_terminator": terminates,
                    "sink_after_guard": sink_line > getattr(node, "end_lineno", node.lineno),
                }
            )
    return {
        "fact_type": "GUARD_ANALYSIS_FACTS",
        "function": focus["function_name"],
        "focus_symbol": symbol,
        "sink_line": sink_line,
        "guard_count": len(guards),
        "guards": guards[:MAX_RESULTS],
        "semantic_safety_proven": False,
        "note": "Guard structure is syntactic evidence only; value semantics and bypassability remain separate validation questions.",
    }


def _symbol_references(root: Path, focus: dict[str, Any]) -> dict[str, Any]:
    symbol = focus["focus_symbol"] or focus["function_name"]
    refs: list[dict[str, Any]] = []
    files_scanned = 0
    for path in _bounded_python_files(root):
        files_scanned += 1
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            match = isinstance(node, ast.Name) and node.id == symbol
            if match:
                refs.append({"artifact": path.relative_to(root).as_posix(), "line": node.lineno})
                if len(refs) >= MAX_RESULTS:
                    break
        if len(refs) >= MAX_RESULTS:
            break
    return {
        "fact_type": "SYMBOL_REFERENCE_FACTS",
        "symbol": symbol,
        "files_scanned": files_scanned,
        "reference_count": len(refs),
        "truncated": len(refs) >= MAX_RESULTS,
        "references": refs,
    }


def _source_context(focus: dict[str, Any], radius: int = 6) -> dict[str, Any]:
    lines = focus["source_text"].splitlines()
    start = max(1, focus["focus_line"] - radius)
    end = min(len(lines), focus["focus_line"] + radius)
    return {
        "fact_type": "SOURCE_CONTEXT_FACTS",
        "artifact": focus["artifact"],
        "start_line": start,
        "end_line": end,
        "focus_line": focus["focus_line"],
        "lines": [
            {"line": number, "text": lines[number - 1]}
            for number in range(start, end + 1)
        ],
    }


def _execute_operation(operation: EvidenceOperation, root: Path, focus: dict[str, Any]) -> dict[str, Any]:
    if operation == EvidenceOperation.CALL_SITE_SEARCH:
        return _call_sites(root, focus["function_name"], focus["parameter_index"])
    if operation == EvidenceOperation.INTERPROCEDURAL_TRACE:
        return _interprocedural_trace(root, focus)
    if operation == EvidenceOperation.GUARD_ANALYSIS:
        return _guard_analysis(focus)
    if operation == EvidenceOperation.SYMBOL_REFERENCE_SEARCH:
        return _symbol_references(root, focus)
    if operation == EvidenceOperation.SOURCE_CONTEXT:
        return _source_context(focus)
    raise EvidenceExecutorError(f"unsupported evidence operation: {operation}")


def _existing_result(ledger: Ledger, proposal_id: str, request: str) -> dict[str, Any] | None:
    wanted = f"Evidence request: {request}"
    with ledger.connect() as conn:
        rows = conn.execute(
            "SELECT id, payload_json FROM objects WHERE kind='Experiment' ORDER BY created_at"
        ).fetchall()
        evidence_rows = conn.execute(
            "SELECT id, payload_json FROM objects WHERE kind='Evidence' ORDER BY created_at"
        ).fetchall()
    for row in rows:
        payload = json.loads(row["payload_json"])
        prov = payload.get("provenance") or {}
        if (
            payload.get("objective") == wanted
            and prov.get("created_by") == "evidence-request-executor-v1.9"
            and proposal_id in (prov.get("parent_ids") or [])
        ):
            evidence_ids = []
            for erow in evidence_rows:
                ep = json.loads(erow["payload_json"])
                if ep.get("experiment_id") == row["id"]:
                    evidence_ids.append(erow["id"])
            return {
                "experiment_id": row["id"],
                "evidence_ids": evidence_ids,
                "method_id": payload.get("method_id"),
            }
    return None


def run_evidence_request_executor(
    ledger: Ledger,
    proposal_id: str,
    repo_root: str | Path,
    *,
    policy: ScopePolicy,
    repo_commit: str | None = None,
) -> dict[str, Any]:
    """Execute a deferred evidence request through a closed deterministic registry."""
    policy.require(Capability.REPO_READ)
    policy.require(Capability.EVIDENCE_COLLECT)
    root = policy.require_repository(repo_root)
    ledger.init()

    proposal = _required(ledger, proposal_id, "ResearchProposal")
    if proposal.get("proposal_kind") != ProposalKind.EVIDENCE_REQUEST.value:
        raise EvidenceExecutorError("only EVIDENCE_REQUEST proposals may enter the evidence executor")
    if proposal.get("disposition") != ProposalDisposition.SEEK_EVIDENCE.value:
        raise EvidenceExecutorError("proposal disposition is not SEEK_EVIDENCE")

    decision_id, decision = _decision_for_proposal(ledger, proposal_id)
    if decision.get("decision") != "DEFER":
        raise EvidenceExecutorError(
            f"proposal gate decision is {decision.get('decision')}, expected DEFER"
        )
    if "EVIDENCE_REQUEST_REQUIRES_EXECUTOR" not in (decision.get("reason_codes") or []):
        raise EvidenceExecutorError("ProposalDecision did not defer this request to the evidence executor")
    if decision.get("subject_id") != proposal.get("subject_id"):
        raise EvidenceExecutorError("ProposalDecision subject does not match proposal subject")

    provenance = proposal.get("provenance") or {}
    if provenance.get("scope_id") != policy.scope_id:
        raise EvidenceExecutorError("proposal scope does not match active scope policy")
    if repo_commit and provenance.get("repo_commit") and provenance.get("repo_commit") != repo_commit:
        raise EvidenceExecutorError("proposal was produced from a different repository commit")

    hypothesis_id = proposal.get("subject_id")
    focus = _focus_context(ledger, hypothesis_id, root)
    requests = list(dict.fromkeys(proposal.get("requested_evidence") or []))
    if not requests:
        raise EvidenceExecutorError("proposal contains no requested evidence")

    classified = [(request, classify_evidence_request(request)) for request in requests]
    supported = [(request, op) for request, op in classified if op is not None]
    if not supported:
        raise EvidenceExecutorError("no requested evidence maps to the V1.9 approved operation registry")

    results: list[dict[str, Any]] = []
    new_items = [(request, op) for request, op in supported if _existing_result(ledger, proposal_id, request) is None]

    method: Method | None = None
    if new_items:
        method = Method(
            name="Bounded deterministic evidence request executor",
            kind=MethodKind.EVIDENCE_EXECUTOR,
            version="1.9",
            deterministic=True,
            parameters={
                "approved_operations": [op.value for op in EvidenceOperation],
                "network": False,
                "shell": False,
                "subprocess": False,
                "exec": False,
                "eval": False,
                "repository_write": False,
                "max_python_files": MAX_PYTHON_FILES,
                "max_file_bytes": MAX_FILE_BYTES,
                "max_results": MAX_RESULTS,
            },
            provenance=Provenance(
                created_by="evidence-request-executor-v1.9",
                tool_name="python-ast-registry",
                tool_version="1.9",
                repo_commit=repo_commit,
                scope_id=policy.scope_id,
                parent_ids=[proposal_id, decision_id, hypothesis_id],
            ),
        )
        ledger.put(method)

    for request, operation in classified:
        if operation is None:
            results.append(
                {
                    "request": request,
                    "operation": None,
                    "status": "UNSUPPORTED",
                    "reason_code": "NO_APPROVED_OPERATION_MAPPING",
                    "experiment_id": None,
                    "evidence_ids": [],
                    "idempotent_reuse": False,
                }
            )
            continue

        existing = _existing_result(ledger, proposal_id, request)
        if existing is not None:
            results.append(
                {
                    "request": request,
                    "operation": operation.value,
                    "status": "COMPLETED",
                    **existing,
                    "idempotent_reuse": True,
                }
            )
            continue

        assert method is not None
        facts = _execute_operation(operation, root, focus)
        facts_json = json.dumps(facts, sort_keys=True, separators=(",", ":"))
        result_hash = sha256_text(facts_json)

        experiment = Experiment(
            hypothesis_id=hypothesis_id,
            method_id=method.id,
            objective=f"Evidence request: {request}",
            procedure=[
                f"Classify request as {operation.value} using the closed V1.9 registry.",
                "Read only authorized repository files through bounded Python AST parsing.",
                "Record syntactic facts without asserting vulnerability support or exploitability.",
            ],
            expected_result="Deterministic repository facts relevant to the requested evidence question.",
            observed_result=f"Collected {facts.get('fact_type')} with SHA-256 {result_hash}.",
            status=ExperimentStatus.COMPLETED,
            provenance=Provenance(
                created_by="evidence-request-executor-v1.9",
                tool_name="python-ast-registry",
                tool_version="1.9",
                repo_commit=repo_commit,
                input_hash=sha256_text(request),
                output_hash=result_hash,
                scope_id=policy.scope_id,
                parent_ids=[proposal_id, decision_id, hypothesis_id, method.id],
            ),
        )
        ledger.put(experiment)

        evidence = Evidence(
            description=(
                f"Deterministic {operation.value} facts collected for deferred ResearchProposal {proposal_id}. "
                "Executor output is neutral evidence and is not a vulnerability conclusion."
            ),
            source_type=SourceType.FILE.value,
            source_ref=f"{focus['artifact']}:{focus['focus_line']}",
            relation=EvidenceRelation.NEUTRAL,
            source_id=focus["source_id"],
            method_id=method.id,
            experiment_id=experiment.id,
            immutable_hash=result_hash,
            metadata={
                "fact_type": facts.get("fact_type"),
                "operation": operation.value,
                "request": request,
                "facts": facts,
                "executor_version": "1.9",
                "interpretation": "NEUTRAL_FACT_COLLECTION",
            },
            provenance=Provenance(
                created_by="evidence-request-executor-v1.9",
                tool_name="python-ast-registry",
                tool_version="1.9",
                repo_commit=repo_commit,
                input_hash=sha256_text(request),
                output_hash=result_hash,
                scope_id=policy.scope_id,
                parent_ids=[proposal_id, decision_id, hypothesis_id, method.id, experiment.id, focus["source_id"]],
            ),
        )
        ledger.put(evidence)

        ledger.add_edge(experiment.id, EdgeRelation.DERIVED_FROM, proposal_id)
        ledger.add_edge(experiment.id, EdgeRelation.DERIVED_FROM, decision_id)
        ledger.add_edge(experiment.id, EdgeRelation.TESTS, hypothesis_id)
        ledger.add_edge(experiment.id, EdgeRelation.USES_METHOD, method.id)
        ledger.add_edge(experiment.id, EdgeRelation.PRODUCES, evidence.id)
        ledger.add_edge(evidence.id, EdgeRelation.DERIVED_FROM, experiment.id)
        ledger.add_edge(evidence.id, EdgeRelation.DERIVED_FROM, proposal_id)
        ledger.add_edge(evidence.id, EdgeRelation.DERIVED_FROM, decision_id)
        ledger.add_edge(evidence.id, EdgeRelation.BEARS_ON, hypothesis_id)
        ledger.add_edge(evidence.id, EdgeRelation.USES_METHOD, method.id)
        ledger.add_edge(evidence.id, EdgeRelation.OBSERVED_FROM, focus["source_id"])

        results.append(
            {
                "request": request,
                "operation": operation.value,
                "status": "COMPLETED",
                "experiment_id": experiment.id,
                "evidence_ids": [evidence.id],
                "method_id": method.id,
                "idempotent_reuse": False,
            }
        )

    audit = ledger.audit()
    if not audit["ok"]:
        raise EvidenceExecutorError(f"executor produced invalid ledger: {audit['issues']}")

    completed = [item for item in results if item["status"] == "COMPLETED"]
    return {
        "proposal_id": proposal_id,
        "decision_id": decision_id,
        "hypothesis_id": hypothesis_id,
        "repository_root": str(root),
        "requests": results,
        "completed_count": len(completed),
        "unsupported_count": sum(item["status"] == "UNSUPPORTED" for item in results),
        "evidence_ids": [eid for item in completed for eid in item["evidence_ids"]],
        "idempotent_reuse": bool(completed) and all(item["idempotent_reuse"] for item in completed),
        "audit": audit,
    }
