from __future__ import annotations

from pathlib import Path

from research_agent.compatible_case import run_compatible_acceptance_case
from research_agent.ledger import Ledger
from research_agent.policy import ScopePolicy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT / "targets" / "contextual_validator_cases"
SIGNALS = REPO_ROOT / "signals.json"
POLICY = PROJECT_ROOT / "policy" / "scope.yaml"


def test_openai_compatible_acceptance_case_is_offline_and_bounded(tmp_path):
    ledger = Ledger(tmp_path / "compatible.db")
    policy = ScopePolicy.load(POLICY)
    result = run_compatible_acceptance_case(
        ledger,
        REPO_ROOT,
        SIGNALS,
        policy=policy,
        repo_commit="v1.8-test",
    )
    assert result["transport"] == "offline-fixture"
    assert result["all_expected"] is True
    assert result["prohibited_objects"] == {}
    assert result["audit"]["ok"] is True
    assert all(item["boundary_pass"] for item in result["proposals"])

    with ledger.connect() as conn:
        rows = conn.execute(
            "SELECT payload_json FROM objects WHERE kind='Method'"
        ).fetchall()
    import json
    model_methods = [
        json.loads(row[0]) for row in rows
        if json.loads(row[0]).get("kind") == "MODEL_REASONING"
    ]
    assert model_methods
    for method in model_methods:
        metadata = method["parameters"].get("adapter_metadata", {})
        if metadata.get("adapter") == "openai-compatible-chat-completions":
            assert metadata["last_request_hash"]
            assert metadata["last_response_hash"]
            assert "super-secret-token" not in json.dumps(metadata)
