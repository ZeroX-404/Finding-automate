from research_agent.cli.main import (
    build_platform,
)



def test_cli_platform_creation():

    platform = build_platform()

    assert platform is not None
