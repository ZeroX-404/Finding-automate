from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from research_agent.autonomous_agent import (
    AutonomousResearchAgent,
)


app = FastAPI(
    title="Autonomous Research Agent API",
    version="7.1",
)


agent = AutonomousResearchAgent()



class ResearchRequest(BaseModel):

    target: str

    hypothesis: str



@app.get("/health")
def health():

    return {
        "status":
        "ok"
    }



@app.post("/research/run")
def run_research(
    request: ResearchRequest,
):

    result = agent.run(
        target=request.target,
        hypothesis=request.hypothesis,
    )

    return result
