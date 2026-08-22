from research_agent.security_scanner import (
    CustomPatternScanner,
)



def test_security_scanner(
    tmp_path,
):

    file = tmp_path / "app.py"

    file.write_text(
        'password="secret"'
    )


    scanner = CustomPatternScanner()


    result = scanner.scan(
        tmp_path
    )


    assert (
        len(result)
        ==
        1
    )


    assert (
        result[0].rule
        ==
        "HARDCODED_SECRET"
    )
