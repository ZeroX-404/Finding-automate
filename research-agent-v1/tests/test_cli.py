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


from typer.testing import CliRunner

from research_agent.cli import app


def test_runtime_info_is_project_anchored():
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["runtime-info"],
    )

    assert result.exit_code == 0
    assert ".research-agent" in result.stdout


def test_real_model_cli_is_denied_by_default_policy_before_network():
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "research-propose-compatible",
            "CAS-does-not-matter",
            "CRT-does-not-matter",
            "targets/contextual_validator_cases",
            "fixture-model",
            "http://127.0.0.1:9/v1",
        ],
    )

    assert result.exit_code == 1

    output = result.stdout
    if result.stderr:
        output += result.stderr

    assert "model:invoke is DENY" in output

