from research_agent.runtime_cli import (
    build_parser,
)


def test_runtime_cli_parser():

    parser = build_parser()

    args = parser.parse_args(
        [
            "run",
            "--hypothesis",
            "HYP-test",
            "--target",
            "./demo",
        ]
    )


    assert args.command == "run"
    assert args.hypothesis == "HYP-test"
