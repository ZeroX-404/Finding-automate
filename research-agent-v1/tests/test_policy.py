from pathlib import Path

from research_agent.policy import Capability, Decision, ScopePolicy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = PROJECT_ROOT / "policy" / "scope.yaml"


def test_v1_denies_active_testing():
    policy = ScopePolicy.load(POLICY_PATH)

    assert policy.decision(Capability.TARGET_TEST) == Decision.DENY
    assert policy.decision(Capability.REPO_WRITE) == Decision.DENY
    assert policy.decision(Capability.EXTERNAL_SUBMIT) == Decision.DENY


def test_v1_allows_static_analysis():
    policy = ScopePolicy.load(POLICY_PATH)

    assert policy.decision(Capability.REPO_READ) == Decision.ALLOW
    assert policy.decision(Capability.STATIC_SCAN) == Decision.ALLOW


def test_repository_allowlist_accepts_nested_target(tmp_path):
    allowed = tmp_path / "targets"
    nested = allowed / "repo"
    nested.mkdir(parents=True)
    policy = ScopePolicy.model_validate(
        {
            "scope_id": "test",
            "repository_roots": [str(allowed)],
            "capabilities": {"repo:read": "ALLOW"},
        }
    )
    assert policy.require_repository(nested) == nested.resolve()


def test_repository_allowlist_rejects_outside_target(tmp_path):
    allowed = tmp_path / "targets"
    allowed.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    policy = ScopePolicy.model_validate(
        {
            "scope_id": "test",
            "repository_roots": [str(allowed)],
            "capabilities": {"repo:read": "ALLOW"},
        }
    )
    import pytest

    with pytest.raises(PermissionError):
        policy.require_repository(outside)
