from __future__ import annotations

import argparse
import json
from pathlib import Path

from research_agent.platform import (
    AutonomousResearchPlatform,
)

from research_agent.repository_scanner import (
    RepositoryIntelligenceScanner,
)

from research_agent.evidence_generator import (
    EvidenceGenerationPipeline,
)

from research_agent.hypothesis_synthesis import (
    HypothesisSynthesisEngine,
)

from research_agent.research_proposal import (
    ResearchProposalGenerator,
)

from research_agent.workflow_composer import (
    ResearchWorkflowComposer,
)


HISTORY_FILE = (
    Path(".research-agent")
    /
    "sessions.json"
)



def build_platform():

    return AutonomousResearchPlatform(

        scanner=
        RepositoryIntelligenceScanner(),

        evidence_pipeline=
        EvidenceGenerationPipeline(),

        hypothesis_engine=
        HypothesisSynthesisEngine(),

        proposal_generator=
        ResearchProposalGenerator(),

        workflow_composer=
        ResearchWorkflowComposer(),

    )



def save_history(result):

    HISTORY_FILE.parent.mkdir(
        exist_ok=True
    )

    history = []

    if HISTORY_FILE.exists():

        history = json.loads(
            HISTORY_FILE.read_text()
        )


    history.append(
        result
    )


    HISTORY_FILE.write_text(
        json.dumps(
            history,
            indent=2,
        )
    )



def show_history():

    if not HISTORY_FILE.exists():

        print(
            "No research history found."
        )

        return


    history = json.loads(
        HISTORY_FILE.read_text()
    )


    for item in history:

        print("=" * 40)

        print(
            "SESSION:",
            item.get(
                "session_id"
            )
        )

        print(
            "Repository:",
            item.get(
                "repository"
            )
        )

        print(
            "Evidence:",
            item.get(
                "evidence"
            )
        )

        print(
            "Hypothesis:",
            item.get(
                "hypotheses"
            )
        )

        print(
            "Workflow:",
            item.get(
                "workflows"
            )
        )



def main():

    parser = argparse.ArgumentParser(
        prog="research-agent"
    )


    sub = parser.add_subparsers(
        dest="command"
    )


    scan = sub.add_parser(
        "scan"
    )

    scan.add_argument(
        "path"
    )


    scan.add_argument(
        "--json",
        action="store_true",
    )


    sub.add_parser(
        "history"
    )


    args = parser.parse_args()



    if args.command == "scan":

        platform = build_platform()


        result = platform.research(
            repository=args.path,
            objective=
            "find security issues",
        )


        save_history(
            result
        )


        if args.json:

            print(
                json.dumps(
                    result,
                    indent=2,
                )
            )

        else:

            print(
                "Autonomous Research Completed"
            )

            print(
                "Repository:",
                result["repository"]
            )

            print(
                "Evidence:",
                result["evidence"]
            )

            print(
                "Hypothesis:",
                result["hypotheses"]
            )

            print(
                "Workflow:",
                result["workflows"]
            )



    elif args.command == "history":

        show_history()



if __name__ == "__main__":

    main()
