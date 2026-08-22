from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json



@dataclass
class GraphNode:

    id: str

    node_type: str

    data: dict



@dataclass
class GraphEdge:

    source: str

    relation: str

    target: str



class PersistentKnowledgeGraph:


    def __init__(
        self,
        path=".research-agent/knowledge_graph.json",
    ):

        self.path = Path(path)

        self.nodes = []

        self.edges = []

        self.load()



    def load(self):

        if not self.path.exists():

            return


        data = json.loads(
            self.path.read_text()
        )


        self.nodes = data.get(
            "nodes",
            []
        )


        self.edges = data.get(
            "edges",
            []
        )



    def save(self):

        self.path.parent.mkdir(
            exist_ok=True
        )


        self.path.write_text(
            json.dumps(
                {
                    "nodes":
                    self.nodes,

                    "edges":
                    self.edges,
                },

                indent=2,
            )
        )



    def add_node(
        self,
        node_id,
        node_type,
        data,
    ):

        self.nodes.append(

            {
                "id":
                node_id,

                "type":
                node_type,

                "data":
                data,
            }

        )

        self.save()



    def add_edge(
        self,
        source,
        relation,
        target,
    ):

        self.edges.append(

            {
                "source":
                source,

                "relation":
                relation,

                "target":
                target,
            }

        )

        self.save()



    def find_node(
        self,
        node_id,
    ):

        for node in self.nodes:

            if node["id"] == node_id:

                return node


        return None
