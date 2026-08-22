from __future__ import annotations


class EvidenceTraversal:

    def __init__(self, ledger):
        self.ledger = ledger


    def neighbors(
        self,
        object_id: str,
    ) -> list[str]:

        graph = self.ledger.export_graph()

        result = []

        for edge in graph["edges"]:

            if edge["source_id"] == object_id:
                result.append(
                    edge["target_id"]
                )

            elif edge["target_id"] == object_id:
                result.append(
                    edge["source_id"]
                )

        return result


    def walk(
        self,
        start_id: str,
        depth: int = 3,
    ) -> list[str]:

        visited = {
            start_id
        }

        frontier = {
            start_id
        }

        for _ in range(depth):

            next_frontier = set()

            for node in frontier:

                for neighbor in self.neighbors(node):

                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_frontier.add(neighbor)

            frontier = next_frontier

            if not frontier:
                break

        return list(visited)
