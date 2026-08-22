from research_agent.adaptive_agent_selector import (
    AdaptiveAgentSelector,
)


class FakeReputation:


    def trust_weight(
        self,
        agent,
    ):

        scores = {
            "ResearcherAgent": 0.95,
            "CriticAgent": 0.55,
        }

        return scores[agent]



def test_choose_best_agent():

    selector = AdaptiveAgentSelector(
        reputation_engine=
        FakeReputation()
    )


    result = selector.choose(
        "REQUEST_MORE_EVIDENCE",
        [
            "ResearcherAgent",
            "CriticAgent",
        ],
    )


    assert (
        result.agent
        ==
        "ResearcherAgent"
    )


    assert (
        result.score
        ==
        0.95
    )
