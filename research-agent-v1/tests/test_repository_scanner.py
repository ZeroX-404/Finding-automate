from research_agent.repository_scanner import (
    RepositoryIntelligenceScanner,
)



def test_repository_scan(
    tmp_path,
):

    file = tmp_path / "app.py"


    file.write_text(
        """
        password="12345"
        """
    )


    scanner = (
        RepositoryIntelligenceScanner()
    )


    result = scanner.scan(
        tmp_path
    )


    assert (
        result.files
        ==
        1
    )


    assert (
        "Python"
        in
        result.languages
    )


    assert (
        len(
            result.suspicious_files
        )
        ==
        1
    )
