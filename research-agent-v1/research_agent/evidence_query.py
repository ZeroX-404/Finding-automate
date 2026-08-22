from __future__ import annotations


class EvidenceQuery:

    def __init__(self, ledger):
        self.ledger = ledger


    def evidence_for(self, object_id: str):

        graph = self.ledger.export_graph()

        result = []

        for edge in graph["edges"]:

            if (
                edge["source_id"] == object_id
                and edge["relation"] == "SUPPORTS"
            ):
                result.append(
                    edge["target_id"]
                )

        return result


    def claims_from_evidence(self, evidence_id: str):

        graph = self.ledger.export_graph()

        result = []

        for edge in graph["edges"]:

            if (
                edge["source_id"] == evidence_id
                and edge["relation"] == "SUPPORTS"
            ):
                result.append(
                    edge["target_id"]
                )

        return result


    def lineage(self, object_id: str):

        graph = self.ledger.export_graph()

        nodes = {
            object_id
        }

        changed = True

        while changed:

            changed = False

            for edge in graph["edges"]:

                if edge["target_id"] in nodes:
                    if edge["source_id"] not in nodes:
                        nodes.add(edge["source_id"])
                        changed = True

                if edge["source_id"] in nodes:
                    if edge["target_id"] not in nodes:
                        nodes.add(edge["target_id"])
                        changed = True

        return list(nodes)
