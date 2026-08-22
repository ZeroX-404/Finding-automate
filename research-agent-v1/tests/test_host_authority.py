from research_agent.host_authority import (
    HostAuthorityEngine,
)



def test_default_permission():

    engine = HostAuthorityEngine()


    result = engine.request(
        "RUN_COMMAND",
        "./repo",
        "execute validation",
    )


    assert (
        result["decision"]
        ==
        "ASK"
    )



def test_allow_override():

    engine = HostAuthorityEngine()


    engine.approve(
        "RUN_COMMAND"
    )


    result = engine.request(
        "RUN_COMMAND",
        "./repo",
        "run test",
    )


    assert (
        result["decision"]
        ==
        "ALLOW"
    )



def test_block_delete():

    engine = HostAuthorityEngine()


    result = engine.request(
        "DELETE_FILE",
        "/tmp/a",
        "cleanup",
    )


    assert (
        result["decision"]
        ==
        "DENY"
    )
