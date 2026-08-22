from research_agent.evidence_generator import (
    EvidenceGenerationPipeline,
)


class FakeReport:

    suspicious_files = [
        "auth.py"
    ]



def test_generate_evidence():


    pipeline = (
        EvidenceGenerationPipeline()
    )


    result = (
        pipeline
        .from_scanner_report(
            FakeReport()
        )
    )


    assert (
        len(result)
        ==
        1
    )


    assert (
        result[0].source
        ==
        "auth.py"
    )


    assert (
        result[0].evidence_type
        ==
        "STATIC_ANALYSIS"
    )
