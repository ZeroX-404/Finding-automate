from fastapi.testclient import TestClient

from research_agent.api import app


client = TestClient(app)



def test_health():

    response = client.get(
        "/health"
    )


    assert (
        response.status_code
        ==
        200
    )


    assert (
        response.json()["status"]
        ==
        "ok"
    )



def test_research_endpoint():

    response = client.post(
        "/research/run",
        json={
            "target":
            "demo",

            "hypothesis":
            "test hypothesis",
        },
    )


    assert (
        response.status_code
        ==
        200
    )


    assert (
        response.json()["status"]
        ==
        "COMPLETED"
    )
