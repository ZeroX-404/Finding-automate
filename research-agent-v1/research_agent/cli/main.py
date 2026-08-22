from __future__ import annotations

import argparse
import json

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


    args = parser.parse_args()


    if args.command == "scan":

        platform = build_platform()


        result = platform.research(

            repository=args.path,

            objective=
            "find security issues",

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
                f"Repository: {result['repository']}"
            )

            print(
                f"Evidence: {result['evidence']}"
            )

            print(
                f"Hypothesis: {result['hypotheses']}"
            )

            print(
                f"Workflow: {result['workflows']}"
            )


if __name__ == "__main__":

    main()
