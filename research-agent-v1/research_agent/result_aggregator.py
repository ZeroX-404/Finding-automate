from __future__ import annotations


class AgentResultAggregator:


    def merge(
        self,
        results: dict,
    ):

        return {
            "agents": list(
                results.keys()
            ),

            "results": results,

            "count": len(results),
        }
