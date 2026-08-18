import json
from pathlib import Path

import pytest

from research_agent.ledger import Ledger
from research_agent.policy import ScopePolicy
from research_agent.signal_pipeline import (
    SignalPipelineError,
    collect_source_context,
    resolve_repo_artifact,
    run_semgrep_signal_pipeline,
)


def policy_for(repo_root: Path) -> ScopePolicy:
    return ScopePolicy.model_validate(
        {
            "scope_id": "test-scope",
            "repository_roots": [str(repo_root)],
            "capabilities": {
                "reason": "ALLOW",
                "repo:read": "ALLOW",
                "scanner:static": "ALLOW",
                "sandbox:execute": "ALLOW",
                "network:read": "DENY",
                "target:test": "DENY",
                "repo:write": "DENY",
                "git:commit": "DENY",
                "external:submit": "DENY",
            },
        }
    )


def write_semgrep(path: Path, artifact: str, line: int = 3) -> None:
    payload = {
        "version": "test",
        "results": [
            {
                "check_id": "python.lang.security.audit.eval-detected",
                "path": artifact,
                "start": {"line": line, "col": 5},
                "end": {"line": line, "col": 24},
                "extra": {
                    "message": "Detected use of eval",
                    "severity": "WARNING",
                    "metadata": {"cwe": ["CWE-95"]},
                },
            }
        ],
    }
    path.write_text(json.dumps(payload))


def test_pipeline_creates_signal_not_finding(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    source = repo / "app.py"
    source.write_text(
        "def calculate(expr):\n"
        "    value = expr\n"
        "    return eval(value)\n"
    )
    semgrep = tmp_path / "semgrep.json"
    write_semgrep(semgrep, "app.py")

    ledger = Ledger(tmp_path / "evidence.db")
    result = run_semgrep_signal_pipeline(
        ledger,
        semgrep,
        repo,
        policy=policy_for(repo),
        repo_commit="abc123",
        context_radius=2,
    )

    assert result["candidate_count"] == 1
    assert result["audit"]["ok"] is True

    candidate = result["candidates"][0]
    trace = ledger.trace(candidate["hypothesis_id"], max_depth=5)
    kinds = {node["kind"] for node in trace["nodes"].values()}
    assert {"Source", "Method", "Observation", "Hypothesis"}.issubset(kinds)

    with ledger.connect() as conn:
        kinds_in_db = {
            row[0] for row in conn.execute("SELECT DISTINCT kind FROM objects").fetchall()
        }
    assert "Finding" not in kinds_in_db
    assert "Claim" not in kinds_in_db
    assert "Validation" not in kinds_in_db

    evidence = ledger.get(candidate["context_evidence_id"])
    assert evidence is not None
    assert evidence["payload"]["relation"] == "NEUTRAL"

    evidence_graph = ledger.graph(candidate["context_evidence_id"])
    assert any(
        edge["relation"] == "BEARS_ON" and edge["target_id"] == candidate["hypothesis_id"]
        for edge in evidence_graph["outgoing"]
    )


def test_context_is_bounded_and_hashed(tmp_path):
    target = tmp_path / "app.py"
    target.write_text("\n".join(f"line-{i}" for i in range(1, 11)) + "\n")
    context = collect_source_context(target, line=5, radius=2)
    assert context["start_line"] == 3
    assert context["end_line"] == 7
    assert "line-5" in context["text"]
    assert "line-8" not in context["text"]


def test_rejects_path_traversal_outside_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "secret.py"
    outside.write_text("secret = True\n")

    with pytest.raises(SignalPipelineError, match="escapes authorized repository root"):
        resolve_repo_artifact(repo, "../secret.py")


def test_rejects_symlink_escape(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("outside = True\n")
    link = repo / "linked.py"
    link.symlink_to(outside)

    with pytest.raises(SignalPipelineError, match="escapes authorized repository root"):
        resolve_repo_artifact(repo, "linked.py")


def test_pipeline_requires_static_analysis_capability(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app.py").write_text("x = 1\n")
    semgrep = tmp_path / "semgrep.json"
    write_semgrep(semgrep, "app.py", line=1)

    policy = policy_for(repo).model_copy(
        update={
            "capabilities": {
                **policy_for(repo).capabilities,
                "scanner:static": "DENY",
            }
        }
    )

    with pytest.raises(PermissionError):
        run_semgrep_signal_pipeline(
            Ledger(tmp_path / "evidence.db"),
            semgrep,
            repo,
            policy=policy,
        )


def test_pipeline_rejects_repository_outside_policy(tmp_path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "app.py").write_text("x = 1\n")
    semgrep = tmp_path / "semgrep.json"
    write_semgrep(semgrep, "app.py", line=1)

    policy = policy_for(allowed)
    with pytest.raises(PermissionError, match="outside configured repository_roots"):
        run_semgrep_signal_pipeline(
            Ledger(tmp_path / "evidence.db"),
            semgrep,
            outside,
            policy=policy,
        )
