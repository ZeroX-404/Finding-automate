from __future__ import annotations


class AutonomousResearchBrain:


    def __init__(
        self,
        strategy_planner,
        execution_graph,
        consensus_engine,
        calibration_engine=None,
        memory=None,
    ):

        self.strategy_planner = strategy_planner
        self.execution_graph = execution_graph
        self.consensus_engine = consensus_engine
        self.calibration_engine = calibration_engine
        self.memory = memory



    def run(
        self,
        hypothesis_id: str,
        context: dict,
    ):

        strategy = (
            self.strategy_planner
            .select_strategy(
                hypothesis_id
            )
        )


        agents = (
            strategy.required_agents
        )


        for agent in agents:

            self.execution_graph.add_agent(
                agent
            )


        results = (
            self.execution_graph.run(
                lambda agent:
                {
                    "agent": agent,
                    "status": "COMPLETED",
                }
            )
        )


        votes = []

        for agent in results:

            votes.append(
                {
                    "agent": agent,
                    "decision": "CONTINUE",
                    "confidence": 0.8,
                }
            )


        consensus = (
            self.consensus_engine.evaluate(
                votes
            )
        )


        if self.memory:

            self.memory.store(
                {
                    "hypothesis_id":
                        hypothesis_id,
                    "strategy":
                        strategy.name,
                    "consensus":
                        consensus,
                }
            )


        return {

            "hypothesis_id":
                hypothesis_id,

            "strategy":
                strategy.name,

            "agents":
                agents,

            "results":
                results,

            "consensus":
                consensus,

        }
