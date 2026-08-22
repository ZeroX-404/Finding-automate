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



def test_platform_creates_audit_trace(tmp_path):

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
        "security analysis",
    )


    assert (
        result["session_id"]
        .startswith("RUN-")
    )


    assert (
        len(
            result["audit"]["events"]
        )
        >=
        4
    )


    assert (
        "EVIDENCE_CREATED"
        in
        [
            x["name"]
            for x
            in
            result["audit"]["events"]
        ]
    )
