from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4



@dataclass
class AgentMessage:

    agent: str

    action: str

    result: str



@dataclass
class SecurityTeamResult:

    id: str = field(
        default_factory=lambda:
        f"TEAM-{uuid4().hex[:12]}"
    )

    messages: list[AgentMessage] = field(
        default_factory=list
    )

    decision: str = ""



class ScoutAgent:


    name = "SCOUT"



    def analyze(
        self,
        finding,
    ):

        return AgentMessage(

            agent=self.name,

            action="ANALYZE_FINDING",

            result=
            (
                f"Evidence collected from "
                f"{finding.file}"
            ),

        )



class CriticAgent:


    name = "CRITIC"



    def analyze(
        self,
        finding,
    ):

        return AgentMessage(

            agent=self.name,

            action="CHALLENGE_FINDING",

            result=
            (
                "Need proof of security impact"
            ),

        )



class ValidatorAgent:


    name = "VALIDATOR"



    def analyze(
        self,
        finding,
    ):

        return AgentMessage(

            agent=self.name,

            action="VALIDATE",

            result=
            (
                "Additional reproduction required"
            ),

        )



class LeadResearcherAgent:



    def decide(
        self,
        messages,
    ):

        result = SecurityTeamResult()


        result.messages.extend(
            messages
        )


        if len(messages) >= 3:

            result.decision = (
                "NEEDS_VALIDATION"
            )

        else:

            result.decision = (
                "INSUFFICIENT_REVIEW"
            )


        return result
