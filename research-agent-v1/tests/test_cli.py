from pathlib import Path

from research_agent.cli import DEFAULT_POLICY_PATH
from research_agent.policy import ScopePolicy


def test_default_policy_path_is_absolute_and_exists():
    path = Path(DEFAULT_POLICY_PATH)

    assert path.is_absolute()
    assert path.exists()
    assert path.name == "scope.yaml"


def test_default_policy_can_load_independent_of_cwd():
    policy = ScopePolicy.load(DEFAULT_POLICY_PATH)

    assert policy.scope_id == "local-security-research-v1"
