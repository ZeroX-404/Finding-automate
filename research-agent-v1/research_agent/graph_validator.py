from __future__ import annotations


class GraphConsistencyValidator:

    def __init__(self, ledger):
        self.ledger = ledger


    def validate(self) -> dict:

        graph = self.ledger.export_graph()

        objects = {
            obj["id"]
            for obj in graph["objects"]
        }

        issues = []


        for edge in graph["edges"]:

            source = edge["source_id"]
            target = edge["target_id"]

            if source not in objects:
                issues.append(
                    f"missing source object: {source}"
                )

            if target not in objects:
                issues.append(
                    f"missing target object: {target}"
                )


        return {
            "ok": len(issues) == 0,
            "objects": len(objects),
            "edges": len(graph["edges"]),
            "issues": issues,
        }
