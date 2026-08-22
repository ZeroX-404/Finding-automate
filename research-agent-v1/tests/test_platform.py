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



def test_platform_pipeline(
    tmp_path,
):

    file = tmp_path / "auth.py"

    file.write_text(
        'password="secret"'
    )


    platform = AutonomousResearchPlatform(

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


    result = platform.research(
        str(tmp_path),
        "find security issues",
    )


    assert (
        result["status"]
        ==
        "COMPLETED"
    )


    assert (
        result["evidence"]
        >
        0
    )


    assert (
        result["workflows"]
        >
        0
    )
